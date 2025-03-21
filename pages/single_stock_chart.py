import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import snowflake.connector

import streamlit as st

st.set_page_config(
    page_title="Single Stock Chart",
    layout="wide",
    page_icon="📈",
)

def get_snowflake_connection():
    return snowflake.connector.connect(
        user=st.secrets["SNOWFLAKE_USER"],
        password=st.secrets["SNOWFLAKE_PW"],
        account=st.secrets["SNOWFLAKE_ACCOUNT"],
        warehouse=st.secrets["SNOWFLAKE_WH"],
        database=st.secrets["SNOWFLAKE_DB"],
        schema='RESEARCHDATA',
    )

def get_growth_stock_data(conn, symbol: str):
    query = """
    SELECT TRADEDATE as "Date",TRADECLOSE as "Close"
    FROM TRADESMITH.HISTORICALDATANEW.STOCKDATA_SVIEW SD INNER JOIN TRADESMITH.HISTORICALDATANEW.SYMBOL_SVIEW S ON S.SymbolId = SD.SymbolId
    WHERE S.Symbol = ?
    ORDER BY TradeDate desc;
    """

    try:
        cur = conn.cursor()
        df = cur.execute(query, params=(symbol.upper()).fetch_pandas_all())

        return df
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return None


with st.form("stock_form"):
    symbol = st.text_input("Enter stock symbol (e.g., AAPL, TSLA):", max_chars=10)
    submitted = st.form_submit_button("Get Chart")

    if submitted:
        if symbol.strip() == "":
            st.warning("Please enter a valid stock symbol.")
        else:
            with st.spinner("Fetching data..."):
                data = get_growth_stock_data(symbol)
                if data.empty:
                    st.error(f"No data found for symbol '{symbol.upper()}'.")
                else:
                    st.success(f"Showing price history for {symbol.upper()}:")
                    data['date'] = pd.to_datetime(data['date'])
                    st.line_chart(data.set_index("date")["price"])
