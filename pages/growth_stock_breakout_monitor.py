import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import snowflake.connector

import streamlit as st

st.set_page_config(
    page_title="Growth Stock Upside Breakout Monitor",
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

def get_growth_stock_data(conn):
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

    try:
        cur = conn.cursor()
        df = cur.execute(query).fetch_pandas_all()
        df['DATE'] = pd.to_datetime(df['DATE'])

        # Ensure MARKETCAP is a float
        if 'MARKETCAP' in df.columns:
            df['MARKETCAP'] = pd.to_numeric(df['MARKETCAP'], errors='coerce')

        return df
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return None


def create_price_chart(ticker_data, symbol):
    display_data = ticker_data.head(252).sort_values('DATE', ascending=True)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=display_data['DATE'],
        y=display_data['ADJCLOSE'],
        mode='lines',
        name=symbol,
        line=dict(color='royalblue', width=2)
    ))

    fig.update_layout(
        title=f"{symbol} - Upside Breakout",
        xaxis_title="Date",
        yaxis_title="Price",
        height=400,
        width=800
    )
    return fig

def generate_analysis(ticker_data, symbol):
    current_row = ticker_data.iloc[0]
    signal_count = ticker_data.head(21)['IS_ONE_MONTH_HIGH'].sum()

    price = current_row['ADJCLOSE']
    market_cap = current_row['MARKETCAP'] / 1e9  # Convert to billions
    industry = current_row['INDUSTRY']

    # Properly format the ordinal suffix
    suffix = "th" if 4 <= signal_count <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(signal_count % 10, "th")

    # Build the properly formatted message
    st.write(f"**Upside Breakout Alert:** ${symbol} just hit a new 1-month high of ${price:,.2f}.")
    st.write(f"${symbol} is a ${market_cap:,.2f} billion market cap member of the {industry} industry group.")
    st.write(f"This marks the {signal_count}{suffix} upside breakout for ${symbol} over the last 21 trading days.")
    

    # alert = (f"**Upside Breakout Alert:** ${symbol} just hit a new 1-month high of ${price:,.2f}. "
    #         f"\r\n${symbol} is a ${market_cap:,.2f} billion market cap member of the {industry} industry group. "
    #         f"\r\nThis marks the {signal_count}{suffix} upside breakout for ${symbol} over the last 21 trading days.")



def main():
    st.title("Growth Stock Upside Breakout Monitor")
    st.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if st.button("🔙 Back to Home"):
        st.query_params["page"] = ""  # Update the query parameters



    with st.spinner("Fetching breakout data..."):
        conn = get_snowflake_connection()
        df = get_growth_stock_data(conn)

        if df is None:
            st.error("Error fetching data.")
            return

        for ticker in df['TICKER'].unique():
            ticker_data = df[df['TICKER'] == ticker]

            st.subheader("$"+ticker)
            generate_analysis(ticker_data, ticker)
            st.plotly_chart(create_price_chart(ticker_data, ticker), use_container_width=True)
            st.divider()

        conn.close()

if __name__ == "__main__":
    main()
