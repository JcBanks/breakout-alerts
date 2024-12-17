# import streamlit as st
# import pandas as pd
# import plotly.graph_objects as go
# from datetime import datetime
# import snowflake.connector

# # Page config
# st.set_page_config(
#     page_title="ETF Breakout Scanner",
#     page_icon="📈",
#     layout="wide"
# )

# # Custom CSS
# st.markdown("""
#     <style>
#     .block-container {padding-top: 1rem;}
#     </style>
#     """, unsafe_allow_html=True)

# def get_snowflake_connection():
#     return snowflake.connector.connect(
#         user=st.secrets["SNOWFLAKE_USER"],
#         password=st.secrets["SNOWFLAKE_PW"],
#         account=st.secrets["SNOWFLAKE_ACCOUNT"],
#         warehouse=st.secrets["SNOWFLAKE_WH"],
#         database=st.secrets["SNOWFLAKE_DB"],
#         schema='RESEARCHDATA',
#     )

# def get_stock_data(conn):
#     query = """
#     select *
#     from (
#     select rsi.*,
#            d.DESCRIPTION,
#                   ADJHIGH = MAX(ADJHIGH) over (
#                partition by rsi.ticker
#                order by date
#                ROWS BETWEEN 21 PRECEDING AND CURRENT ROW
#            ) as is_one_month_high,
#         ADJHIGH = MAX(ADJHIGH) over (
#                partition by rsi.ticker
#                order by date
#                ROWS BETWEEN 252 PRECEDING AND CURRENT ROW
#            ) as is_one_year_high,
#         ADJLOW = MIN(ADJLOW) over (
#                partition by rsi.ticker
#                order by date
#                ROWS BETWEEN 21 PRECEDING AND CURRENT ROW
#            ) as is_one_month_low,
#         ADJLOW = MIN(ADJLOW) over (
#                partition by rsi.ticker
#                order by date
#                ROWS BETWEEN 252 PRECEDING AND CURRENT ROW
#            ) as is_one_year_low
#     from RESEARCHDATA.YF_STOCK_RSI_DATA rsi
#     JOIN RESEARCHDATA.ETF_DESCRIPTIONS d on d.TICKER = rsi.TICKER
#     where ISETF
#     order by rsi.TICKER desc, date desc)
#     qualify last_value(is_one_month_high) over (partition by ticker order by date) = true 
#         or last_value(is_one_month_low) over (partition by ticker order by date) = true
#     order by ticker desc, date desc;
#     """
    
#     try:
#         cur = conn.cursor()
#         df = cur.execute(query).fetch_pandas_all()
#         df['DATE'] = pd.to_datetime(df['DATE'])
#         return df
#     except Exception as e:
#         st.error(f"Error fetching data: {str(e)}")
#         return None

# def create_price_chart(ticker_data, symbol, breakout_type):
#     display_data = ticker_data.head(21).sort_values('DATE', ascending=True)
    
#     fig = go.Figure()
#     fig.add_trace(go.Scatter(
#         x=display_data['DATE'],
#         y=display_data['ADJCLOSE'],
#         mode='lines',
#         name=symbol,
#         line=dict(
#             color='royalblue',
#             width=2
#         ),
#         showlegend=False
#     ))

#     fig.update_layout(
#         title={
#             'text': f"{symbol} - {'Upward' if breakout_type == 'high' else 'Downward'} Breakout",
#             'y':0.9,
#             'x':0.5,
#             'xanchor': 'center',
#             'yanchor': 'top',
#             'font': dict(size=16)
#         },
#         paper_bgcolor='white',
#         plot_bgcolor='white',
#         width=1250,
#         height=400,
#         margin=dict(l=40, r=40, t=60, b=40),
#         xaxis=dict(
#             showgrid=True,
#             gridcolor='#E5E5E5',
#             dtick='D1',
#             tickformat='%b %d',
#             tickangle=-45,
#             showline=True,
#             linewidth=1,
#             linecolor='#CCCCCC'
#         ),
#         yaxis=dict(
#             showgrid=True,
#             gridcolor='#E5E5E5',
#             showline=True,
#             linewidth=1,
#             linecolor='#CCCCCC',
#             tickprefix='$',
#             tickformat='.2f'
#         )
#     )
#     return fig

# def generate_analysis(ticker_data, symbol, breakout_type):
#     current_row = ticker_data.iloc[0]
#     signal_count = 0
    
#     recent_data = ticker_data.head(21)
    
#     if breakout_type == 'high':
#         signal_count = recent_data['IS_ONE_MONTH_HIGH'].sum()
#         price = current_row['ADJHIGH']
#         timeframe = "high" if current_row['IS_ONE_YEAR_HIGH'] else "1 month high"
#         alert_type = "Upside"
#     else:
#         signal_count = recent_data['IS_ONE_MONTH_LOW'].sum()
#         price = current_row['ADJLOW']
#         timeframe = "low" if current_row['IS_ONE_YEAR_LOW'] else "1 month low"
#         alert_type = "Downside"
    
#     alert = f"""{alert_type} Breakout Alert: {current_row['SHORTNAME']} ({symbol}) just hit a new {timeframe} at ${price:.2f}.
# {current_row['DESCRIPTION']}
# This marks the {signal_count}{'st' if signal_count == 1 else 'nd' if signal_count == 2 else 'rd' if signal_count == 3 else 'th'} {alert_type.lower()} breakout signal for {symbol} over the last 21 trading days."""
    
#     return alert

# def main():
#     st.title("ETF Breakout Scanner")
#     st.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
#     with st.spinner("Fetching breakout data..."):
#         conn = get_snowflake_connection()
#         df = get_stock_data(conn)
        
#         if df is None:
#             st.error("Error fetching data.")
#             return
        
#         breakouts = {'highs': [], 'lows': []}
        
#         # Process breakouts
#         for ticker in df['TICKER'].unique():
#             ticker_data = df[df['TICKER'] == ticker].copy()
#             latest = ticker_data.iloc[0]
            
#             if latest['IS_ONE_MONTH_HIGH']:
#                 breakouts['highs'].append({
#                     'symbol': ticker,
#                     'data': ticker_data
#                 })
#             elif latest['IS_ONE_MONTH_LOW']:
#                 breakouts['lows'].append({
#                     'symbol': ticker,
#                     'data': ticker_data
#                 })

#         # Display results using Streamlit components
#         col1, col2 = st.columns(2)
        
#         with col1:
#             if breakouts['highs']:
#                 st.header("🔼 NEW 1-MONTH HIGHS")
#                 for breakout in breakouts['highs']:
#                     st.subheader(breakout['symbol'])
#                     st.write(generate_analysis(
#                         breakout['data'],
#                         breakout['symbol'],
#                         'high'
#                     ))
#                     st.plotly_chart(
#                         create_price_chart(breakout['data'], breakout['symbol'], 'high'),
#                         use_container_width=True
#                     )
#                     st.divider()
        
#         with col2:
#             if breakouts['lows']:
#                 st.header("🔽 NEW 1-MONTH LOWS")
#                 for breakout in breakouts['lows']:
#                     st.subheader(breakout['symbol'])
#                     st.write(generate_analysis(
#                         breakout['data'],
#                         breakout['symbol'],
#                         'low'
#                     ))
#                     st.plotly_chart(
#                         create_price_chart(breakout['data'], breakout['symbol'], 'low'),
#                         use_container_width=True
#                     )
#                     st.divider()
        
#         if not (breakouts['highs'] or breakouts['lows']):
#             st.info("No breakouts found in the scanned symbols.")
        
#         conn.close()

# if __name__ == "__main__":
#     main()

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import snowflake.connector

# Page config
st.set_page_config(
    page_title="ETF Breakout Scanner",
    page_icon="📈",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .block-container {padding-top: 1rem;}
    </style>
    """, unsafe_allow_html=True)

def get_snowflake_connection():
    return snowflake.connector.connect(
        user=st.secrets["SNOWFLAKE_USER"],
        password=st.secrets["SNOWFLAKE_PW"],
        account=st.secrets["SNOWFLAKE_ACCOUNT"],
        warehouse=st.secrets["SNOWFLAKE_WH"],
        database=st.secrets["SNOWFLAKE_DB"],
        schema='RESEARCHDATA',
    )

def get_stock_data(conn):
    query = """
    select *
    from (
    select rsi.*,
           d.DESCRIPTION,
                  ADJHIGH = MAX(ADJHIGH) over (
               partition by rsi.ticker
               order by date
               ROWS BETWEEN 21 PRECEDING AND CURRENT ROW
           ) as is_one_month_high,
        ADJHIGH = MAX(ADJHIGH) over (
               partition by rsi.ticker
               order by date
               ROWS BETWEEN 252 PRECEDING AND CURRENT ROW
           ) as is_one_year_high,
        ADJLOW = MIN(ADJLOW) over (
               partition by rsi.ticker
               order by date
               ROWS BETWEEN 21 PRECEDING AND CURRENT ROW
           ) as is_one_month_low,
        ADJLOW = MIN(ADJLOW) over (
               partition by rsi.ticker
               order by date
               ROWS BETWEEN 252 PRECEDING AND CURRENT ROW
           ) as is_one_year_low
    from RESEARCHDATA.YF_STOCK_RSI_DATA rsi
    JOIN RESEARCHDATA.ETF_DESCRIPTIONS d on d.TICKER = rsi.TICKER
    where ISETF
    order by rsi.TICKER desc, date desc)
    qualify last_value(is_one_month_high) over (partition by ticker order by date) = true 
        or last_value(is_one_month_low) over (partition by ticker order by date) = true
    order by ticker desc, date desc;
    """
    
    try:
        cur = conn.cursor()
        df = cur.execute(query).fetch_pandas_all()
        df['DATE'] = pd.to_datetime(df['DATE'])
        return df
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return None

def create_price_chart(ticker_data, symbol, breakout_type):
    display_data = ticker_data.head(21).sort_values('DATE', ascending=True)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=display_data['DATE'],
        y=display_data['ADJCLOSE'],
        mode='lines',
        name=symbol,
        line=dict(
            color='royalblue',
            width=2
        ),
        showlegend=False
    ))

    # Add logo as background image
    fig.add_layout_image(
        dict(
            source="assets/Alta_light.png",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            sizex=0.6,  # Adjust size as needed
            sizey=0.6,  # Adjust size as needed
            xanchor="center",
            yanchor="middle",
            opacity=0.1,  # Adjust opacity as needed
            layer="below"
        )
    )

    fig.update_layout(
        title={
            'text': f"{symbol} - {'Upward' if breakout_type == 'high' else 'Downward'} Breakout",
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=16)
        },
        paper_bgcolor='white',
        plot_bgcolor='white',
        width=1250,
        height=400,
        margin=dict(l=40, r=40, t=60, b=40),
        xaxis=dict(
            showgrid=True,
            gridcolor='#E5E5E5',
            dtick='D1',
            tickformat='%b %d',
            tickangle=-45,
            showline=True,
            linewidth=1,
            linecolor='#CCCCCC'
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#E5E5E5',
            showline=True,
            linewidth=1,
            linecolor='#CCCCCC',
            tickprefix='$',
            tickformat='.2f'
        )
    )
    return fig

def generate_analysis(ticker_data, symbol, breakout_type):
    current_row = ticker_data.iloc[0]
    signal_count = 0
    
    recent_data = ticker_data.head(21)
    
    if breakout_type == 'high':
        signal_count = recent_data['IS_ONE_MONTH_HIGH'].sum()
        price = current_row['ADJHIGH']
        timeframe = "high" if current_row['IS_ONE_YEAR_HIGH'] else "1 month high"
        alert_type = "Upside"
    else:
        signal_count = recent_data['IS_ONE_MONTH_LOW'].sum()
        price = current_row['ADJLOW']
        timeframe = "low" if current_row['IS_ONE_YEAR_LOW'] else "1 month low"
        alert_type = "Downside"
    
    alert = f"""{alert_type} Breakout Alert: {current_row['SHORTNAME']} ({symbol}) just hit a new {timeframe} at ${price:.2f}.
{current_row['DESCRIPTION']}
This marks the {signal_count}{'st' if signal_count == 1 else 'nd' if signal_count == 2 else 'rd' if signal_count == 3 else 'th'} {alert_type.lower()} breakout signal for {symbol} over the last 21 trading days."""
    
    return alert

def main():
    st.title("ETF Breakout Scanner")
    st.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    with st.spinner("Fetching breakout data..."):
        conn = get_snowflake_connection()
        df = get_stock_data(conn)
        
        if df is None:
            st.error("Error fetching data.")
            return
        
        breakouts = {'highs': [], 'lows': []}
        
        # Process breakouts
        for ticker in df['TICKER'].unique():
            ticker_data = df[df['TICKER'] == ticker].copy()
            latest = ticker_data.iloc[0]
            
            if latest['IS_ONE_MONTH_HIGH']:
                breakouts['highs'].append({
                    'symbol': ticker,
                    'data': ticker_data
                })
            elif latest['IS_ONE_MONTH_LOW']:
                breakouts['lows'].append({
                    'symbol': ticker,
                    'data': ticker_data
                })

        # Display results using Streamlit components
        col1, col2 = st.columns(2)
        
        with col1:
            if breakouts['highs']:
                st.header("🔼 NEW 1-MONTH HIGHS")
                for breakout in breakouts['highs']:
                    st.subheader(breakout['symbol'])
                    st.write(generate_analysis(
                        breakout['data'],
                        breakout['symbol'],
                        'high'
                    ))
                    st.plotly_chart(
                        create_price_chart(breakout['data'], breakout['symbol'], 'high'),
                        use_container_width=True
                    )
                    st.divider()
        
        with col2:
            if breakouts['lows']:
                st.header("🔽 NEW 1-MONTH LOWS")
                for breakout in breakouts['lows']:
                    st.subheader(breakout['symbol'])
                    st.write(generate_analysis(
                        breakout['data'],
                        breakout['symbol'],
                        'low'
                    ))
                    st.plotly_chart(
                        create_price_chart(breakout['data'], breakout['symbol'], 'low'),
                        use_container_width=True
                    )
                    st.divider()
        
        if not (breakouts['highs'] or breakouts['lows']):
            st.info("No breakouts found in the scanned symbols.")
        
        conn.close()

if __name__ == "__main__":
    main()
