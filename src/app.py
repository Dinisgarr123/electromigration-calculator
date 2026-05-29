 # app.py

"""
IP Electromigration Solver - Frontend Orchestrator

This module serves as the primary Streamlit interface for the EM Sign-off 
Workspace. It manages:
1. PDK Initialization: Dynamically loads technology rules via `tech_rules`.
2. Input Configuration: Provides a sidebar for users to define design parameters.
3. Execution Engine: Orchestrates calls to `em_formulas` and `optimizer` to 
   compute electrical and geometric viability.
4. Visualization: Displays compliance analysis panels and strategy matrices.
"""


import pandas as pd

import streamlit as st

import tech_rules as tech

import em_formulas as em

import optimizer as opt


st.set_page_config(page_title="IP Electromigration Solver", layout="wide")

st.title("⚡ Power Device Macro EM Sign-Off Workspace")


# 1. Dynamic Technology Node Ingestion

# 1. Dynamic Technology Node Ingestion
try:
    available_stacks = tech.get_available_stacks()
    selected_stack = st.sidebar.selectbox("🎯 Target Technology Stack", available_stacks)
    stack_rules = tech.get_stack_rules(selected_stack)
except Exception as e:
    st.error(f"⚠️ Initialization Error: {e}")
    st.stop()


# --- SIDEBAR: DESIGN ENVIRONMENT INPUTS ---

st.sidebar.header("🛠️ Macro Design Environment")


# Block A: General Array Topology Configuration
with st.sidebar.expander("📊 Global Array Configurations", expanded=True):
    # Everything below here MUST have 4 spaces of indentation
    designed_current = st.number_input("Designed Current (mA)", min_value=1.0, value=1350.0, step=50.0)
    max_temp = st.selectbox("Maximum Operating Temperature (°C)", [70, 85, 100, 110, 125, 150], index=3)
    
    col_a, col_b = st.columns(2)
    with col_a:
        num_cols = st.number_input("# of Columns", min_value=1, value=8, step=1)
        w_coeff = st.number_input("W Coefficient", min_value=0.1, value=1.0)
    with col_b:
        num_rows = st.number_input("# of Rows", min_value=1, value=10, step=1)
        l_coeff = st.number_input("L Coefficient", min_value=0.1, value=1.0)


# Extract options safely from parsed stack rules

metal_options = list(stack_rules["metals"].keys()) if stack_rules and stack_rules.get("metals") else ["M4"]

via_options = list(stack_rules["vias"].keys()) if stack_rules and stack_rules.get("vias") else ["contact"]


# Block B: Horizontal Physical Layout
with st.sidebar.expander("🟥 Horizontal Layer Layout", expanded=True):
    horizontal_stack_options = ["M4", "M3", "M2", "M3 + M4", "M2 + M3", "M2 + M3 + M4"]
    selected_h_metal = st.selectbox("Horizontal Metal Stack Combination", horizontal_stack_options, index=0)
    device_w_used = st.number_input("Device W Used (µm)", min_value=1.0, value=45.0)
    h_stripe_w = st.number_input("Horizontal Stripe W (µm)", min_value=0.1, value=20.0)
    h_space_w = st.number_input("Space Between Stripes (µm)", min_value=0.01, value=1.41)
    metal_pairs = st.number_input("# of Metal Pairs", min_value=1, value=1)

# Block C: Vertical Physical Layout
with st.sidebar.expander("🟩 Vertical Layer Layout", expanded=True):
    vertical_stack_options = ["M2", "M3", "M2 + M3", "M3 + M4", "M4 + M5"]
    selected_v_metal = st.selectbox("Vertical Metal Stack Combination", vertical_stack_options, index=0)
    length_unit = st.number_input("Length of Unit Cell (µm)", min_value=1.0, value=47.7)
    num_fingers = st.number_input("# of Fingers", min_value=2, value=50, step=2)
    v_stripe_w = st.number_input("Vertical Stripe W (µm)", min_value=0.01, value=0.7)
    v_space_w = st.number_input("Vertical Space between Stripes (µm)", min_value=0.01, value=0.24)

# Block D: Local Finger Contact Specifications
with st.sidebar.expander("🦿 Power Device Local Core Layout", expanded=True):
    selected_via_layer = st.selectbox("Vertical Via Junction", via_options, index=0)
    contacts_per_finger = st.number_input("Contacts per Finger", min_value=1, value=115)
    m1_vias_per_finger = st.number_input("Metal 1 Vias per Finger", min_value=1, value=72)
    st.markdown("---")
    m1_width = st.number_input("Metal 1 Drawing Width (µm)", min_value=0.0, value=0.40, step=0.05)
    m2_width = st.number_input("Metal 2 Drawing Width (µm)", min_value=0.0, value=0.00, step=0.05)

# --- EXECUTE THE CALCULATION CORES ---
total_units = num_cols * num_rows
current_per_unit = designed_current / total_units if total_units > 0 else 0.0

h_res = em.calculate_horizontal_configuration(
    stack_rules=stack_rules, selected_stack=selected_stack, max_temp=max_temp,
    current_per_unit=current_per_unit, num_cols=num_cols, h_metal_comb=selected_h_metal,
    h_stripe_w=h_stripe_w, h_space_w=h_space_w, metal_pairs=metal_pairs, w_coeff=w_coeff, l_coeff=l_coeff
)

v_res = em.calculate_vertical_configuration(
    stack_rules=stack_rules, selected_stack=selected_stack, max_temp=max_temp,
    current_per_unit=current_per_unit, device_w_used=device_w_used, h_stripe_w=h_stripe_w,
    v_metal_comb=selected_v_metal, v_stripe_w=v_stripe_w, v_space_w=v_space_w, num_fingers=num_fingers,
    metal_pairs=metal_pairs, w_coeff=w_coeff, l_coeff=l_coeff
)

core_res = em.calculate_power_device_unit_info(
    stack_rules=stack_rules, selected_stack=selected_stack, max_temp=max_temp,
    current_per_unit=current_per_unit, selected_via_layer=selected_via_layer,
    contacts_per_finger=contacts_per_finger, m1_vias_per_finger=m1_vias_per_finger,
    num_fingers=num_fingers, metal_pairs=metal_pairs, m1_width=m1_width, m2_width=m2_width,
    w_coeff=w_coeff, l_coeff=l_coeff
)


core_res = em.calculate_power_device_unit_info(

stack_rules=stack_rules, selected_stack=selected_stack, max_temp=max_temp,

current_per_unit=current_per_unit, selected_via_layer=selected_via_layer,

contacts_per_finger=contacts_per_finger, m1_vias_per_finger=m1_vias_per_finger,

num_fingers=num_fingers, metal_pairs=metal_pairs, m1_width=m1_width, m2_width=m2_width,

w_coeff=w_coeff, l_coeff=l_coeff

)



# TOP-LEVEL TELEMETRY VIEW ---

m1, m2, m3 = st.columns(3)

m1.metric("Current per Unit Cell", f"{current_per_unit:.2f} mA")

m2.metric("Total Active Grid Map", f"{total_units} Cells", f"{num_cols}x{num_rows} Geometry")

m3.metric("Total Designed Load", f"{designed_current:.1f} mA")


# Background references safely hidden out of immediate view
with st.expander("📄 View Secondary PDK Meta Details & Source Documents", expanded=False):
    st.caption(f"**PDK Stack Reference Source:** `{selected_stack}`")
    st.caption(f"**PDK Documentation Source Link:** `{stack_rules.get('source_doc', 'N/A')}`")



# --- UI VERIFICATION REPORT PANELS ---
st.markdown("---")
st.subheader("🏁 Sign-off Compliance Analysis Panels")

panel_h, panel_v, panel_core = st.columns(3)

with panel_h:
    st.markdown("### 🟥 Horizontal Bus")
    st.metric("Needed per Row", f"{h_res['current_needed_per_row']:.2f} mA")
    st.metric("Metal Density", f"{h_res['calculated_metal_density_pct']:.2f} %")
    
    # Status bar
    if h_res['pass']:
        st.success(f"✅ **PASS** | Max: {h_res['max_current_per_row']:.2f} mA")
    else:
        st.error(f"❌ **FAIL** | Max: {h_res['max_current_per_row']:.2f} mA")
        
    # Non-overlap factor pinned to the bottom of this panel
    st.caption(f"📐 Non-overlap Factor: `{v_res['non_overlapped_area']:.3f}`")

with panel_v:
    st.markdown("### 🟩 Vertical Feeder")
    st.metric("Needed per Column", f"{v_res['current_needed_per_column']:.2f} mA")
    st.metric("Metal Density", f"{v_res['calculated_metal_density_pct']:.2f} %")
    
    # Status bar
    if v_res['pass']:
        st.success(f"✅ **PASS** | Max: {v_res['max_current_per_column']:.2f} mA")
    else:
        st.error(f"❌ **FAIL** | Max: {v_res['max_current_per_column']:.2f} mA")
    
    # Invisible spacer to match the height of the caption in column 1
    st.write("") 

with panel_core:
    st.markdown("### 🦿 Power Device Local Core")
    
    # Prepare data for the table
    core_data = [
        {
            "Item": "Contacts", 
            "Total": int(core_res['contacts_per_unit']), 
            "Cap (mA)": core_res['max_current_contacts'], 
            "Req (mA)": current_per_unit,
            "Status": "✅" if core_res['contact_pass'] else "❌"
        },
        {
            "Item": "M1 Vias", 
            "Total": int(core_res['vias_per_unit']), 
            "Cap (mA)": core_res['max_current_vias'], 
            "Req (mA)": current_per_unit,
            "Status": "✅" if core_res['via_pass'] else "❌"
        },
        {
            "Item": "S/D Metal", 
            "Total": "-", 
            "Cap (mA)": core_res['max_current_sd_metal'], 
            "Req (mA)": core_res['current_needed_per_segment'],
            "Status": "✅" if core_res['sd_metal_pass'] else "❌"
        }
    ]
    
    # Display as a clean table
    st.table(core_data)
    
    # Add a small legend or note below if needed
    st.caption("Cap: Max Capacity | Req: Requirement")

# --- STRATEGY SWEEP MATRIX ---
st.markdown("---")
st.subheader("📊 Matrix Core Strategy Panel Lookup")

with st.expander("🛠️ Inspect 'horizontal metal configurations' active validation matrix", expanded=True):
    st.write("This grid mirrors the exact layout logic options from your spreadsheet sheet rows.")
    
    # CHANGE THIS: Call em.get_horizontal_matrix instead of the deleted optimizer function
    comb_matrix = em.get_horizontal_matrix(
        stack_rules, selected_stack, max_temp, h_stripe_w, metal_pairs, w_coeff, l_coeff
    )
    
    clean_user_selection = selected_h_metal.replace(" ", "")
    matrix_rows = []
    
    for formula_name, max_curr_capacity in comb_matrix.items():
        is_active = formula_name.replace(" ", "") == clean_user_selection
        
        matrix_rows.append({
            "Horizontal Metal Option Choice": formula_name,
            "Total Parallel Max Current (mA)": max_curr_capacity,
            "Valid? (Active Flag Match)": "🎯 ACTIVE" if is_active else "0.00 mA",
            "Resolved Safe Routing Cap": max_curr_capacity if is_active else 0.0
        })
        
    df_matrix = pd.DataFrame(matrix_rows)
    
    def highlight_active_row(row):
        if row["Valid? (Active Flag Match)"] == "🎯 ACTIVE":
            return ['background-color: rgba(46, 164, 79, 0.15); font-weight: bold; color: #2ea44f;'] * len(row)
        return [''] * len(row)

    st.dataframe(
        df_matrix.style.apply(highlight_active_row, axis=1),
        use_container_width=True,
        hide_index=True
    )
    
    st.info(f"💡 **Excel Sign-Off Output:** Selected Combo **{selected_h_metal}** provides **{h_res['max_current_per_row']:.1f} mA** max capacity. The baseline benchmark single-layer width recommended is **{h_res['best_metal_width']:.2f} µm**.")
