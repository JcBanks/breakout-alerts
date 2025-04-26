import streamlit as st
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

# Database Query Function 

def get_growth_stock_data():
    df = pd.DataFrame(data[])
    with get_snowflake_connection() as conn:
        query = """
        select *
        from (
        select rsi.*,
               f.INDUSTRY,
               f.MARKETCAP,
               qsh.fundamental_score,
               qsh.date quantum_score_date,
               ADJCLOSE = MAX(ADJCLOSE) over (
                   partition by rsi.ticker
                   order by rsi.date rows between 20 preceding and current row
               ) as is_one_month_high,
               -- Check if current close is equal to max close over past year
               ADJCLOSE = MAX(ADJCLOSE) over (
                   partition by rsi.ticker
                   order by rsi.date rows between 251 preceding and current row
               ) as is_one_year_high,
               -- Check if current close is equal to min close over past month
               ADJCLOSE = MIN(ADJCLOSE) over (
                   partition by rsi.ticker
                   order by rsi.date rows between 20 preceding and current row
               ) as is_one_month_low,
               -- Check if current close is equal to min close over past year
               ADJCLOSE = MIN(ADJCLOSE) over (
                   partition by rsi.ticker
                   order by rsi.date rows between 251 preceding and current row
               ) as is_one_year_low
        from RESEARCHDATA.YF_STOCK_RSI_DATA rsi
            join FMP_DATA.FMP_STOCK_SCREENER f on f.SYMBOL = rsi.TICKER
            join (
                select s.SYMBOL,
                       qsh.*
                from RESEARCHDATA.QUANTUM_SCORE_HISTORY qsh
                join HISTORICALDATANEW.SYMBOL_SVIEW s on qsh.SYMBOL_ID = s.SYMBOLID
                where s.DELISTED = false
                and case when ISDUPLICATE then 1 else 0 end = 0
                and qsh.FUNDAMENTAL_SCORE >= 60
                qualify qsh.DATE = last_value(qsh.DATE) over (order by qsh.DATE)
            ) qsh on qsh.SYMBOL = rsi.ticker
        where 1=1
        -- AND insp500
        order by rsi.TICKER desc, rsi.date desc)
        qualify last_value(is_one_month_high) over (partition by ticker order by date) = true
        order by ticker, date desc;
        """
        cur = conn.cursor()
        df = cur.execute(query).fetch_pandas_all()
        df['DATE'] = pd.to_datetime(df['DATE'])
    return df

# Main Display Logic
def show_growth_stock_monitor():
    st.title("Growth Stock Breakout Monitor")
    st.markdown("Explore today's top growth stock breakouts! 📈")

    #df = get_growth_stock_data()
    df = pd.read_csv('growth.csv.zip')

    if df.empty:
        st.info("No breakout stocks found at the moment. 📉 Come back later!")
        return

    for ticker in df['TICKER'].unique():
        stock_data = df[df['TICKER'] == ticker].iloc[0]

        st.subheader(f"{stock_data['COMPANY_NAME']} ({ticker})")

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
