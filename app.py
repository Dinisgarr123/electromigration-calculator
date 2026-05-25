import streamlit as st

st.set_page_config(page_title="EM Calculator", layout="wide")

st.title("⚡ Electromigration Calculator")

# -----------------------
# INPUTS
# -----------------------
st.header("Inputs")

col1, col2 = st.columns(2)

with col1:
    technology = st.selectbox(
        "Technology",
        ["TECH_A", "TECH_B"]
    )

    current = st.number_input("Current (mA)", value=100.0)

    temperature = st.number_input("Temperature (°C)", value=125.0)

with col2:
    width = st.number_input("Width (µm)", value=1.0)
    rows = st.number_input("Rows", value=1)
    cols = st.number_input("Columns", value=1)

st.divider()

# -----------------------
# CALCULATE BUTTON
# -----------------------
if st.button("Calculate EM"):

    # TEMPORARY DUMMY LOGIC (we replace later)
    horizontal_margin = 0.15
    vertical_margin = -0.05

    st.header("Results")

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Horizontal EM")

        if horizontal_margin > 0:
            st.success(f"PASS — Margin: {horizontal_margin*100:.1f}%")
        else:
            st.error(f"FAIL — Margin: {horizontal_margin*100:.1f}%")

    with col4:
        st.subheader("Vertical EM")

        if vertical_margin > 0:
            st.success(f"PASS — Margin: {vertical_margin*100:.1f}%")
        else:
            st.error(f"FAIL — Margin: {vertical_margin*100:.1f}%")

    st.divider()

    st.subheader("Recommendation")

    st.write("Best configuration: M3 + M4 (dummy result)")