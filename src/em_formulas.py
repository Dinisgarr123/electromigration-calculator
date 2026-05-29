import tech_rules as tech
import optimizer

# em_formulas.py
METAL_STACK_MAP = {
    "M2": ["M2"],
    "M2+M3": ["M2", "M3"],
    "M2+M3+M4": ["M2", "M3", "M4"],
    "M3": ["M3"],
    "M3+M4": ["M3", "M4"],
    "M4": ["M4"],
    "M2+M3+M4+MD": ["M2", "M3", "M4", "MD"],
    "M3+M4+MD": ["M3", "M4", "MD"],
    "M4+MD": ["M4", "MD"],
    "MD": ["MD"]
}

def get_single_metal_capacity(stack_rules, selected_stack, max_temp, metal, stripe_w, metal_pairs, w_coeff, l_coeff):
    """

    Computes the EM-limited curren capacity for a specific metal layer.

    This function applies derating factors based on temperature and gemoetry coefficients to determine the maximum allowable current (mA) for a single metal strip segment.

    Args:
        stack_rules (dict): Dictionary containing the PDK metal specifications.
        selected_stack (str): Identifier for the technology process node.
        max_temp (int): Operating temperature in Celsius.
        metal (str): Metal layer name (e.g., "M1", "M2").
        stripe_w (float): Physical drawing width of the metal stripe (µm).
        metal_pairs (int): Number of parallel routing pairs.
        w_coeff (float): Global width derating coefficient.
        l_coeff (float): Global length/loading derating coefficient.

    Returns:
        float: Total allowable current capacity in mA.
    """

    meta = stack_rules["metals"].get(metal, {})
    if not meta: return 0.0
    
    # Physics math extracted from your loop
    temp_factor = tech.get_temp_factor(selected_stack, metal, max_temp)
    eff_w = (meta.get("wpar", 1.0) * stripe_w) - meta.get("reduction", 0.0)
    return (meta.get("current_mA", 0.0) * eff_w * temp_factor * w_coeff * l_coeff * metal_pairs)

def get_horizontal_matrix(stack_rules, selected_stack, max_temp, stripe_w, metal_pairs, w_coeff, l_coeff):
    """

    Generates a lookup matrix of current capacities for all defined horizontal metal combinations.

    Args:
        stack_rules (dict): PDK ruleset.
        selected_stack (str): Active technology stack.
        max_temp (int): Operating temperature (°C).
        stripe_w (float): Stripe drawing width (µm).
        metal_pairs (int): Number of parallel pairs.
        w_coeff (float): Width derating factor.
        l_coeff (float): Length/loading derating factor.

    Returns:
        dict: Mapping of metal combination strings (e.g., "M2+M3") to total capacity (mA).
    """

    matrix = {}
    for name, metals in METAL_STACK_MAP.items():
        # Sum the capacity of all metals in this specific combination
        total = sum(get_single_metal_capacity(stack_rules, selected_stack, max_temp, m, stripe_w, metal_pairs, w_coeff, l_coeff) for m in metals)
        matrix[name] = round(total, 2)
    return matrix


def get_vertical_matrix(stack_rules, selected_stack, max_temp, stripe_w, num_fingers, w_coeff, l_coeff):
    """
    Generates a lookup matrix of current capacities for vertical feeder metal combinations.

    Args:
        stack_rules (dict): PDK ruleset.
        selected_stack (str): Active technology stack.
        max_temp (int): Operating temperature (°C).
        stripe_w (float): Vertical stripe width (µm).
        num_fingers (int): Number of device fingers.
        w_coeff (float): Width derating factor.
        l_coeff (float): Length/loading derating factor.

    Returns:
        dict: Mapping of metal combination strings to total capacity (mA).
    """

    matrix = {}
    for name, metals in METAL_STACK_MAP.items():
        
        # Vertical uses (num_fingers / 2.0) instead of metal_pairs
        total = sum(get_single_metal_capacity(stack_rules, selected_stack, max_temp, m, stripe_w, 1, w_coeff, l_coeff) for m in metals)
        matrix[name] = round(total * (num_fingers / 2.0), 2)
    return matrix
    

def calculate_horizontal_configuration(stack_rules, selected_stack, max_temp, current_per_unit, num_cols, h_metal_comb, h_stripe_w, h_space_w, metal_pairs, w_coeff, l_coeff):
    """
    Performs EM sign-off validation for the horizontal power bus configuration.

    Args:
        current_per_unit (float): Current requirement per unit cell.
        num_cols (int): Total number of columns in the array.
        h_metal_comb (str): User-selected metal combination string (e.g., "M2+M3").
        h_stripe_w (float): Horizontal stripe width (µm).
        h_space_w (float): Horizontal spacing between stripes (µm).
        metal_pairs (int): Number of parallel routing pairs.
        w_coeff (float): Global width derating coefficient.
        l_coeff (float): Global length/loading derating coefficient.

    Returns:
        dict: Validation results including pass/fail status and density metrics.
    """
    
    current_needed_per_row = num_cols * current_per_unit

    # 1. Fetch capacity matrix: Retrieves a lookup table of max current
    comb_matrix = get_horizontal_matrix(stack_rules, selected_stack, max_temp, h_stripe_w, metal_pairs, w_coeff, l_coeff)

    # 2. Extract capacity: Map the user's string selection to the calculated matrix value.
    clean_key = h_metal_comb.replace(" ", "")
    matched_max_current = comb_matrix.get(clean_key, 0.0)

    # 3. Geometric and Density Calculations: 
    # Determines the utilization ratio and the metal fill density.
    # Total width includes all stripes and the gaps between them.
    current_ratio_pct = (matched_max_current / current_per_unit) * 100.0 if current_per_unit > 0 else 0.0
    num_spaces = (metal_pairs * 2) - 1
    total_w_stripes_space = ((h_stripe_w + h_stripe_w) * metal_pairs) + (num_spaces * h_space_w)

    # Density is (Metal Area / Total Area), excluding empty spacing
    calculated_metal_density_pct = ((total_w_stripes_space - (num_spaces * h_space_w)) / total_w_stripes_space) * 100.0 if total_w_stripes_space > 0 else 0.0


    # 4. Sign-off Determination: Compare total array demand against matrix-derived supply

    pass_status = matched_max_current >= current_needed_per_row
    return {
        "current_needed_per_row": current_needed_per_row,
        "max_current_per_row": matched_max_current,
        "current_ratio_pct": current_ratio_pct,
        "total_w_stripes_space": total_w_stripes_space,
        "calculated_metal_density_pct": calculated_metal_density_pct,
        "pass": pass_status
    }

def calculate_vertical_configuration(stack_rules, selected_stack, max_temp, current_per_unit, device_w_used, h_stripe_w, v_metal_comb, v_stripe_w, v_space_w, num_fingers, metal_pairs, w_coeff, l_coeff):
    """
    Performs EM sign-off validation for vertical feeder metal configurations.

    This function calculates the maximum current capacity of the vertical backbone 
    and adjusts the demand based on the non-overlapped area factor relative to 
    the horizontal bus.

    Args:
        current_per_unit (float): Current requirement per unit cell.
        device_w_used (float): Total device width used (µm).
        h_stripe_w (float): Width of the horizontal feeder (µm).
        v_metal_comb (str): Selected vertical metal combination (e.g., "M2+M3").
        v_stripe_w (float): Vertical stripe width (µm).
        v_space_w (float): Vertical space between stripes (µm).
        num_fingers (int): Total number of device fingers.
        # ... (other args match get_vertical_matrix)

    Returns:
        dict: Validation results including non-overlapped area factor, 
              current capacities, density metrics, and pass/fail status.
    """
    # 1. Retrieve the capacity matrix: Fetches the pre-calculated capacity 
    # for all vertical combinations defined in the technology rules.
    clean_v_key = v_metal_comb.replace(" ", "")
    v_matrix = get_vertical_matrix(stack_rules, selected_stack, max_temp, v_stripe_w, num_fingers, w_coeff, l_coeff)
    
    # 2. Extract capacity: Map the user's selected combination string to the capacity value.
    total_max_current_per_column = v_matrix.get(clean_v_key, 0.0)
    
    # 3. Area Intersect Adjustments: 
    # Normalizes the current requirement by calculating the overlap ratio 
    # between the horizontal bus width and the total device width.
    non_overlapped_area = float(h_stripe_w) / float(device_w_used) if device_w_used > 0 else 1.0
    if non_overlapped_area > 1.0:
        non_overlapped_area = 1.0 / non_overlapped_area
        
    current_needed_per_unit_vert = current_per_unit * non_overlapped_area
    current_needed_per_column = current_needed_per_unit_vert

    # 4. Pass/Fail Logic: Compares total backbone supply against the normalized current demand per column.
    if current_needed_per_column == 0.0:
        current_ratio_pct = "DIV/0"
        pass_status = total_max_current_per_column >= current_per_unit
    else:
        current_ratio_pct = (total_max_current_per_column / current_needed_per_column) * 100.0
        pass_status = total_max_current_per_column >= current_needed_per_column

    # 5. Vertical Geometry Metrics: 
    # Computes the total track footprint and current metal density percentage.
    total_w_stripes_space = (v_stripe_w * num_fingers) + (v_space_w * (num_fingers - 1))
    calculated_metal_density_pct = (1.0 - (v_space_w / v_stripe_w)) * 100.0 if v_stripe_w > 0 else 0.0
    
    return {
        "non_overlapped_area": non_overlapped_area,
        "current_needed_per_unit_vert": current_needed_per_unit_vert,
        "current_needed_per_column": current_needed_per_column,
        "max_current_per_column": total_max_current_per_column,
        "current_ratio_pct": current_ratio_pct,
        "total_w_stripes_space": total_w_stripes_space,
        "calculated_metal_density_pct": calculated_metal_density_pct,
        "pass": pass_status
    }

def calculate_power_device_unit_info(stack_rules, selected_stack, max_temp, current_per_unit, selected_via_layer, contacts_per_finger, m1_vias_per_finger, num_fingers, metal_pairs, m1_width, m2_width, w_coeff, l_coeff):
    """
    Validates local power device interconnects (contacts, M1 vias, and local metal segments).

    Args:
        selected_via_layer (str): Selected via technology layer.
        contacts_per_finger (int): Number of contact cuts per finger.
        m1_vias_per_finger (int): Number of M2/M1 via cuts per finger.
        m1_width (float): M1 routing width.
        m2_width (float): M2 routing width.

    Returns:
        dict: Capacity and pass/fail status for contacts, vias, and local metal segments.
    """

    final_coefficient = tech.get_temp_factor(selected_stack, "M1", max_temp) * w_coeff * l_coeff
    
    # 1. Get contanct capacity
    contact_meta = stack_rules["vias"].get("contact")
    if not contact_meta:
        raise ValueError("❌ 'contact' via level not found in tech rules.")
    i_max_contact = contact_meta.get("i_max_base_mA")
    
    # 2. Calculate total current capacity for contacts based on the number of contacts per finger and the number of fingers, then apply the final coefficient.
    contacts_per_unit = contacts_per_finger * (num_fingers / 2.0)
    max_current_contacts = final_coefficient * contacts_per_unit * i_max_contact
    contact_pass = max_current_contacts >= current_per_unit

    # 2. Get M1 Vias capacity:
    m1_via_meta = stack_rules["vias"].get("M2_M1")
    if not m1_via_meta:
        raise ValueError("❌ 'M2_M1' via level not found in tech rules.")
    i_max_m1_via = m1_via_meta.get("i_max_base_mA")
    
    vias_per_unit = m1_vias_per_finger * (num_fingers / 2.0)
    max_current_vias = final_coefficient * vias_per_unit * i_max_m1_via
    via_pass = max_current_vias >= current_per_unit

    # 3. Source/Drain Local Finger Metal Stripe Segment
    if (metal_pairs * num_fingers) > 0:
        current_needed_per_segment = current_per_unit / (metal_pairs * (num_fingers / 2.0))
    else:
        current_needed_per_segment = 0.0

    m1_meta = stack_rules["metals"].get("M1", {})
    m2_meta = stack_rules["metals"].get("M2", {})
    m1_cap = -m1_meta.get("reduction", 0.0) + (m1_meta.get("wpar", 1.0) / m1_width) + (m1_meta.get("current_mA", 1.0) * m1_width) if m1_width > 0 else 0.0
    m2_cap = -m2_meta.get("reduction", 0.0) + (m2_meta.get("wpar", 1.0) / m2_width) + (m2_meta.get("current_mA", 1.0) * m2_width) if m2_width > 0 and "M2" in stack_rules["metals"] else 0.0
    
    max_current_sd_metal = m1_cap + m2_cap
    sd_metal_pass = max_current_sd_metal >= current_needed_per_segment

    return {
        "contacts_per_unit": contacts_per_unit,
        "max_current_contacts": max_current_contacts,
        "contact_pass": contact_pass,
        "vias_per_unit": vias_per_unit,
        "max_current_vias": max_current_vias,
        "via_pass": via_pass,
        "current_needed_per_segment": current_needed_per_segment,
        "max_current_sd_metal": max_current_sd_metal,
        "sd_metal_pass": sd_metal_pass
    }