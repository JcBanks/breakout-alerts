import streamlit as st
from streamlit_extras.switch_page_button import switch_page

st.set_page_config(
    page_title="Project Blizzard Dashboard",
    layout="wide",
    page_icon="📊",
)

st.title("Breakout Monitor Dashboard")
st.markdown("Welcome to the Project Blizzard Dashboard! Choose one of the monitors below:")

col1, col2 = st.columns(2)

# ETF Breakout Monitor Tile
with col1:
    st.image("assets/Alta_light.png", width=100)
    if st.button("ETF Breakout Monitor"):
        switch_page("etf_breakout_monitor")

# Growth Stock Monitor Tile
with col2:
    st.image("assets/Alta_light.png", width=100)
    if st.button("Growth Stock Monitor"):
        switch_page("growth_stock_breakout_monitor")

