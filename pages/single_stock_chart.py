import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import snowflake.connector
from streamlit_date_picker import date_range_picker, date_picker, PickerType
from dateutil.relativedelta import relativedelta


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
    query = f"""
    SELECT TRADEDATE as "Date",TRADECLOSE as "Close"
    FROM TRADESMITH.HISTORICALDATANEW.STOCKDATA_SVIEW SD INNER JOIN TRADESMITH.HISTORICALDATANEW.SYMBOL_SVIEW S ON S.SymbolId = SD.SymbolId
    WHERE S.Symbol = '{symbol.upper()}'
    ORDER BY TradeDate desc;
    """

    try:
        cur = conn.cursor()
        df = cur.execute(query).fetch_pandas_all()

        return df
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return None

def create_price_chart(ticker_data, symbol, start, end):
    display_data = ticker_data.head(252).sort_values('Date', ascending=True)
    
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=display_data['Date'],
        y=display_data['Close'],
        mode='lines',
        name=symbol,
        line=dict(color='royalblue', width=2)
    ))

    fig.update_layout(
        title=f"{symbol}",
        xaxis_title="Date",
        yaxis_title="Price",
        height=400,
        width=800
    )

    fig.update_layout(xaxis_range=[start,end])

    return fig

with st.form("stock_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        symbol = st.text_input("Enter stock symbol (e.g., AAPL, TSLA):", max_chars=10)

    with col2:
        st.write("Enter date range (default 1 year)")
        default_start, default_end = datetime.now() - relativedelta(years=1), datetime.now()

        date_range_string = date_range_picker(picker_type=PickerType.date,
                                              start=default_start, end=default_end,
                                              key='date_range_picker')
        if date_range_string:
            start, end = date_range_string
            st.write(f"Date Range Picker [{start}, {end}]")
    
    with col3:
        st.write("Submit")
        submitted = st.form_submit_button("Get Chart")

    if submitted:
        if symbol.strip() == "":
            st.warning("Please enter a valid stock symbol.")
        else:
            with st.spinner("Fetching data..."):
                conn = get_snowflake_connection()
                data = get_growth_stock_data(conn,symbol)
                if data.empty:
                    st.error(f"No data found for symbol '{symbol.upper()}'.")
                else:
                    st.success(f"Showing price history for {symbol.upper()}:")
                    st.plotly_chart(create_price_chart(data, symbol.upper(), start, end), use_container_width=True)
                    st.dataframe(data)
                conn.close()
