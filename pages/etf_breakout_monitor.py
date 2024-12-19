import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import snowflake.connector

# Utility function to get Snowflake connection
def get_snowflake_connection():
    return snowflake.connector.connect(
        user=st.secrets["SNOWFLAKE_USER"],
        password=st.secrets["SNOWFLAKE_PW"],
        account=st.secrets["SNOWFLAKE_ACCOUNT"],
        warehouse=st.secrets["SNOWFLAKE_WH"],
        database=st.secrets["SNOWFLAKE_DB"],
        schema='RESEARCHDATA',
    )

# Fetch data from Snowflake
def get_stock_data(conn):
    query = """
    SELECT *
    FROM (
        SELECT rsi.*,
               d.DESCRIPTION,
               ADJCLOSE = MAX(ADJCLOSE) OVER (
                   PARTITION BY rsi.ticker
                   ORDER BY date ROWS BETWEEN 20 PRECEDING AND CURRENT ROW
               ) AS is_one_month_high,
               ADJCLOSE = MIN(ADJCLOSE) OVER (
                   PARTITION BY rsi.ticker
                   ORDER BY date ROWS BETWEEN 20 PRECEDING AND CURRENT ROW
               ) AS is_one_month_low
        FROM RESEARCHDATA.YF_STOCK_RSI_DATA rsi
        JOIN RESEARCHDATA.ETF_DESCRIPTIONS d ON d.TICKER = rsi.TICKER
        WHERE ISETF
        ORDER BY rsi.TICKER DESC, date DESC)
    QUALIFY LAST_VALUE(is_one_month_high) OVER (PARTITION BY ticker ORDER BY date) = TRUE 
        OR LAST_VALUE(is_one_month_low) OVER (PARTITION BY ticker ORDER BY date) = TRUE
    ORDER BY ticker DESC, date DESC;
    """
    try:
        cur = conn.cursor()
        df = cur.execute(query).fetch_pandas_all()
        df['DATE'] = pd.to_datetime(df['DATE'])
        return df
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return None

# Generate chart for ETF breakout
def create_price_chart(ticker_data, symbol, breakout_type):
    display_data = ticker_data.head(252).sort_values('DATE', ascending=True)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(len(display_data))),
        y=display_data['ADJCLOSE'],
        mode='lines',
        name=symbol,
        line=dict(color='royalblue', width=2),
        showlegend=False
    ))
    fig.update_layout(
        title=f"{symbol} - {'Upside' if breakout_type == 'high' else 'Downside'} Breakout",
        paper_bgcolor='white',
        width=1250,
        height=400
    )
    return fig

def etf_breakout_monitor():
    # Back to Home button at the top
    if st.button("⬅️ Back to Home"):
        st.session_state["page"] = "Home"
        return

    st.title("ETF Breakout Scanner")
    st.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    with st.spinner("Fetching breakout data..."):
        conn = get_snowflake_connection()
        df = get_stock_data(conn)

        if df is None:
            st.error("Error fetching data.")
            return

        breakouts = {'highs': [], 'lows': []}
        for ticker in df['TICKER'].unique():
            ticker_data = df[df['TICKER'] == ticker].copy()
            latest = ticker_data.iloc[0]
            if latest['IS_ONE_MONTH_HIGH']:
                breakouts['highs'].append({'symbol': ticker, 'data': ticker_data})
            elif latest['IS_ONE_MONTH_LOW']:
                breakouts['lows'].append({'symbol': ticker, 'data': ticker_data})

        col1, col2 = st.columns(2)

        with col1:
            if breakouts['highs']:
                st.header("🔼 NEW 1-MONTH HIGHS")
                for breakout in breakouts['highs']:
                    st.subheader(breakout['symbol'])
                    st.plotly_chart(create_price_chart(breakout['data'], breakout['symbol'], 'high'))
                    st.divider()

        with col2:
            if breakouts['lows']:
                st.header("🔽 NEW 1-MONTH LOWS")
                for breakout in breakouts['lows']:
                    st.subheader(breakout['symbol'])
                    st.plotly_chart(create_price_chart(breakout['data'], breakout['symbol'], 'low'))
                    st.divider()

        if not (breakouts['highs'] or breakouts['lows']):
            st.info("No breakouts found in the scanned symbols.")
        conn.close()

