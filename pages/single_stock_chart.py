import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import snowflake.connector
from streamlit_datetime_range_picker import datetime_range_picker


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

def create_price_chart(ticker_data, symbol):
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
    return fig

with st.form("stock_form"):
    symbol = st.text_input("Enter stock symbol (e.g., AAPL, TSLA):", max_chars=10)
    # Use date_range_picker to create a datetime range picker
    st.subheader('Date Range Picker')
    date_range_string = date_range_picker(picker_type=PickerType.time.string_value,
                                          start=-30, end=0, unit=Unit.days.string_value,
                                          key='range_picker',
                                          refresh_button={'is_show': True, 'button_name': 'Reset',
                                                          'refresh_date': -30,
                                                          'unit': Unit.days.string_value})
    if date_range_string is not None:
        start_datetime = date_range_string[0]
        end_datetime = date_range_string[1]
        st.write(f"Date Range Picker [{start_datetime}, {end_datetime}]")
    
    st.subheader('Date Picker')
    # Use date_picker to create a date picker
    date_string = date_picker(picker_type=PickerType.time.string_value, value=0, unit=Unit.days.string_value,
                              key='date_picker')
    
    if date_string is not None:
    st.write('Date Picker: ', date_string)
    
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
                    st.plotly_chart(create_price_chart(data, symbol.upper()), use_container_width=True)
                    st.dataframe(data)
                conn.close()
