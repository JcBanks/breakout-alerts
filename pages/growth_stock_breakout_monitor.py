import streamlit as st
import pandas as pd
from utils.database import get_snowflake_connection
from utils.helpers import format_percentage, format_currency

# Set page configuration
st.set_page_config(
    page_title="Growth Stock Breakout Monitor",
    layout="wide",
    page_icon="🌟",
)

# Initialize session state for navigation
if 'view' not in st.session_state:
    st.session_state.view = 'growth'


# Main Display Logic
def show_growth_stock_monitor():
    st.title("Growth Stock Breakout Monitor")
    st.markdown("Explore today's top growth stock breakouts! 📈")

    # Database Query Function with Caching
    with get_snowflake_connection() as conn:
        query = """
            SELECT
                TICKER,
                COMPANY_NAME,
                CLOSE_DATE,
                CLOSE_PRICE,
                BREAKOUT_LEVEL,
                BREAKOUT_PERCENT,
                BREAKOUT_VOLUME_PERCENT
            FROM
                BREAKOUT_ALERTS.GROWTH_STOCK_MONITOR
            WHERE
                CLOSE_DATE = CURRENT_DATE()
            ORDER BY
                BREAKOUT_PERCENT DESC
        """
    df = conn.query(query)


    if df.empty:
        st.info("No breakout stocks found at the moment. 📉 Come back later!")
        return

    for ticker in df['TICKER'].unique():
        stock_data = df[df['TICKER'] == ticker].iloc[0]

        st.subheader("$"+ticker)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(label="Breakout Level", value=format_currency(stock_data['BREAKOUT_LEVEL']))
            st.metric(label="Breakout %", value=format_percentage(stock_data['BREAKOUT_PERCENT']))

        with col2:
            st.metric(label="Close Price", value=format_currency(stock_data['CLOSE_PRICE']))

        with col3:
            st.metric(label="Volume vs Average", value=format_percentage(stock_data['BREAKOUT_VOLUME_PERCENT']))

        st.markdown("<hr style='border:1px solid #ccc;'>", unsafe_allow_html=True)

# Render Page Based on Session State
def render_page():
    if st.session_state.view == 'growth':
        show_growth_stock_monitor()
    else:
        st.error("Unknown page! Taking you back to safety. 🚧")
        st.session_state.view = 'growth'
        show_growth_stock_monitor()

# Actually run the page
render_page()
