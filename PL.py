import streamlit as st
from PIL import Image

# Set page configuration
st.set_page_config(
    page_title="Premier League Analytics",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premier League colors
PL_PRIMARY_COLOR = "#37003C"
PL_HOVER_COLOR = "#500050"
PL_TEXT_COLOR = "#FFFFFF"

# Custom CSS for large buttons
st.markdown(f"""
    <style>
    div.stButton > button {{
        width: 100%;
        height: 200px;
        font-size: 2em;
        background-color: {PL_PRIMARY_COLOR};
        color: {PL_TEXT_COLOR};
        border: none;
        border-radius: 16px;
        margin: 10px;
        transition: background-color 0.3s ease;
    }}
    div.stButton > button:hover {{
        background-color: {PL_HOVER_COLOR};
        color: {PL_TEXT_COLOR};
    }}
    </style>
""", unsafe_allow_html=True)

# Title
st.markdown("<h1 style='text-align: center; color: #37003C;'>⚽ Premier League 2024/2025 Analytics</h1>", unsafe_allow_html=True)
st.markdown("---")

# Create a full-page grid with large buttons
col1, col2 = st.columns(2)

with col1:
    if st.button("📈 Team Dashboard"):
        st.switch_page("pages/Team_Dashboard.py")
    if st.button("🔍 Player Analysis"):
        st.switch_page("pages/Player_Analysis.py")



with col2:
    if st.button("⚽️ Best XI (TOTS)"):
        st.switch_page("pages/TOTS.py")

    if st.button("📊 Player Comparison"):
        st.switch_page("pages/Player_Comparison.py")



# Footer
st.markdown("""
    <br><br>
    <div style='text-align: center; color: #37003C;'>
        Built with passion for Premier League fans ⚽️
    </div>
""", unsafe_allow_html=True)

st.markdown(
    "<div style='text-align:center; margin-top:50px; color:gray;'>© 2025 Houssem Aridhi</div>",
    unsafe_allow_html=True
)
