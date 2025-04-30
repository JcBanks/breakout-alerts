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
            select *
        from (
        select rsi.*,
            d.DESCRIPTION,
            -- Check if current close is equal to max close over past month
            ADJCLOSE = MAX(ADJCLOSE) over (
                partition by rsi.ticker
                order by date rows between 20 preceding and current row
            ) as is_one_month_high,
            -- Check if current close is equal to max close over past year
            ADJCLOSE = MAX(ADJCLOSE) over (
                partition by rsi.ticker
                order by date rows between 251 preceding and current row
            ) as is_one_year_high,
            -- Check if current close is equal to min close over past month
            ADJCLOSE = MIN(ADJCLOSE) over (
                partition by rsi.ticker
                order by date rows between 20 preceding and current row
            ) as is_one_month_low,
            -- Check if current close is equal to min close over past year
            ADJCLOSE = MIN(ADJCLOSE) over (
                partition by rsi.ticker
                order by date rows between 251 preceding and current row
            ) as is_one_year_low
        from RESEARCHDATA.YF_STOCK_RSI_DATA rsi
        JOIN RESEARCHDATA.ETF_DESCRIPTIONS d on d.TICKER = rsi.TICKER
        where ISETF
        order by rsi.TICKER desc, date desc)
        qualify last_value(is_one_month_high) over (partition by ticker order by date) = true 
            or last_value(is_one_month_low) over (partition by ticker order by date) = true
        order by ticker desc, date desc;
        """
        # Create cursor
        cursor = conn.cursor()
        try:
            cursor.execute(query)
            df = cursor.fetch_pandas_all()
        finally:
            cursor.close()

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
