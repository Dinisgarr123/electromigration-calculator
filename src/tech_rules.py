"""
tech_rules.py

This module manages the ingestion of PDK (Process Design Kit) parameters from Excel/ODS
files. It provides a centralized interface for the application to query metal capacities, 
via ratings, and temperature derating factors.

Expected Excel Structure (Sheet: 'PDK_Signoff_Rules'):
    - Keywords like 'METAL_TABLE_START' and 'METAL_TABLE_END' are required to 
      delimit data blocks.
    - Metal tables expect columns: [Type, Name, current_mA, reduction, wpar, mA_per_W, Res].
"""

import pandas as pd
import os

_CACHED_DATABASE = None

def clean_cell(val):
    """Sanitizes spreadsheet inputs by stripping whitespace and handling non-numeric tokens."""
    if pd.isna(val):
        return None
    s = str(val).strip()
    if s in ["-", "", "#VALUE!", "nan"]:
        return None
    return s

def find_valid_pdk_file():
    """Locates the PDK source file in the application directory."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    for fmt in [{"filename": "pdk_rules.ods", "engine": "odf"}, {"filename": "pdk_rules.xlsx", "engine": "openpyxl"}]:
        full_path = os.path.join(current_dir, fmt["filename"])
        if os.path.exists(full_path):
            return full_path, fmt["engine"]
    return None, None

def initialize_database_from_excel():
    """
    Parses the PDK spreadsheet and caches the structured dictionary.
    
    Returns:
        dict: A nested dictionary keyed by stack name containing all rule tables.
    """
    global _CACHED_DATABASE
    if _CACHED_DATABASE is not None:
        return _CACHED_DATABASE

    file_path, engine = find_valid_pdk_file()
    if not file_path:
        raise FileNotFoundError("❌ Missing 'pdk_rules.ods' or 'pdk_rules.xlsx'")

    try:
        df = pd.read_excel(file_path, sheet_name="PDK_Signoff_Rules", header=None, engine=engine)
        raw_preview = []
        for idx, row in df.head(15).iterrows():
            row_list = [str(cell).strip() for cell in row]
            raw_preview.append(f"Row {idx+1}: {row_list}")

        stack_name = "Unknown Stack"
        source_doc = "Unknown Document Link"
        metals, vias, temp_factors_mx, temp_factors_ix, geometry_rules = {}, {}, {}, {}, []
        in_metal, in_via, in_temp, in_geom = False, False, False, False

        for _, row in df.iterrows():
            col0 = str(row[0]).strip() if pd.notna(row[0]) else ""
            keyword = col0.upper()

            if "STACK_NAME" in keyword:
                stack_name = clean_cell(row[1]) if len(row) > 1 else "Unknown"
                continue
            elif "DOC_REF" in keyword:
                source_doc = f"{clean_cell(row[1])} ({clean_cell(row[2])})" if len(row) > 2 else "Unknown"
                continue
            elif keyword == "METAL_TABLE_START": in_metal = True; continue
            elif keyword == "METAL_TABLE_END": in_metal = False; continue
            elif keyword == "VIA_TABLE_START": in_via = True; continue
            elif keyword == "VIA_TABLE_END": in_via = False; continue
            elif keyword == "TEMP_TABLE_START": in_temp = True; continue
            elif keyword == "TEMP_TABLE_END": in_temp = False; continue
            elif keyword == "GEOMETRY_TABLE_START": in_geom = True; continue
            elif keyword == "GEOMETRY_TABLE_END": in_geom = False; continue

            if in_metal:
                layer_name = clean_cell(row[1])
                if not layer_name or "LEVEL" in layer_name.upper():
                    continue
                try:
                    metals[layer_name] = {
                        "metal_type": clean_cell(row[0]),
                        "current_mA": float(row[2]) if clean_cell(row[2]) else 0.0,
                        "reduction": float(row[3]) if clean_cell(row[3]) else 0.0,
                        "wpar": float(row[4]) if clean_cell(row[4]) else 1.0,
                        "mA_per_W_base": float(row[5]) if clean_cell(row[5]) else 0.0,
                        "resistance_mOhm_um2": float(row[6]) if clean_cell(row[6]) else 0.0
                    }
                except Exception:
                    continue
            elif in_via and keyword == "VIA":
                via_name = clean_cell(row[1])
                if via_name:
                    try:
                        vias[via_name] = {
                            "i_max_base_mA": float(row[2]) if clean_cell(row[2]) else 0.0
                        }
                    except Exception:
                        continue
            elif in_temp and keyword == "TEMP":
                try:
                    if clean_cell(row[1]) and clean_cell(row[2]) and str(row[2]).strip() != "-":
                        temp_factors_mx[int(float(row[1]))] = float(row[2])
                    if clean_cell(row[3]) and clean_cell(row[4]) and str(row[4]).strip() != "-":
                        temp_factors_ix[int(float(row[3]))] = float(row[4])
                except Exception:
                    continue
            elif in_geom and keyword == "GEOM":
                geometry_rules.append({
                    "metal_type": clean_cell(row[1]),
                    "length_condition": clean_cell(row[2]),
                    "width_condition": clean_cell(row[3]),
                    "factor_override": clean_cell(row[4])
                })

        _CACHED_DATABASE = {
            stack_name: {
                "metals": metals, "vias": vias,
                "temp_factors_mx": temp_factors_mx, "temp_factors_ix": temp_factors_ix,
                "geometry_rules": geometry_rules, "source_doc": source_doc,
                "_raw_preview": raw_preview
            }
        }
        return _CACHED_DATABASE
    except Exception as e:
        raise ValueError(f"Spreadsheet read failure: {e}")

def get_temp_factor(stack_name, metal_layer, temperature):
    """
    Calculates the temperature derating factor for a specific metal layer.
    
    Args:
        stack_name (str): Identifier for the technology stack.
        metal_layer (str): Name of the layer (e.g., "M1").
        temperature (int/float): Operating temperature.
    """
    db = initialize_database_from_excel()
    stack = db.get(stack_name)
    if not stack: raise ValueError(f"Stack '{stack_name}' not found.")
    layer_info = stack["metals"].get(metal_layer)
    if not layer_info: raise ValueError(f"Layer '{metal_layer}' is not configured.")
    m_type = layer_info["metal_type"]
    factors = stack["temp_factors_ix"] if m_type in ["Ix", "Ox"] else stack["temp_factors_mx"]
    return factors.get(int(temperature), 1.0)

def get_stack_rules(stack_name):
    """Returns all rules for a given stack."""
    return initialize_database_from_excel().get(stack_name, None)

def get_available_stacks():
    """Returns a list of all defined technology stacks in the database."""
    return list(initialize_database_from_excel().keys())