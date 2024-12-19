import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import snowflake.connector
import base64


# Custom CSS
st.markdown("""
    <style>
    .block-container {padding-top: 1rem;}
    </style>
    """, unsafe_allow_html=True)

def get_image_as_base64():
    try:
        with open("assets/Alta_light.png", "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except Exception as e:
        st.warning(f"Could not load logo: {str(e)}")
        return None

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
    
    try:
        cur = conn.cursor()
        df = cur.execute(query).fetch_pandas_all()
        df['DATE'] = pd.to_datetime(df['DATE'])
        return df
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return None

def create_price_chart(ticker_data, symbol, breakout_type):
    # Take 252 trading days (1 year) and sort by date
    display_data = ticker_data.head(252).sort_values('DATE', ascending=True)
    
    # Get base64 encoded logo
    logo_base64 = get_image_as_base64()
    
    fig = go.Figure()
    
    # Main price line
    fig.add_trace(go.Scatter(
        x=list(range(len(display_data))),
        y=display_data['ADJCLOSE'],
        mode='lines',
        name=symbol,
        line=dict(
            color='royalblue',
            width=2
        ),
        showlegend=False
    ))

    # Add logo as background image if available
    if logo_base64:
        fig.add_layout_image(
            dict(
                source=f"data:image/png;base64,{logo_base64}",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                sizex=0.6,
                sizey=0.6,
                xanchor="center",
                yanchor="middle",
                opacity=0.1,
                layer="below"
            )
        )

    # Calculate tick positions for approximately monthly intervals
    tick_positions = list(range(0, len(display_data), 21))  # Show one tick per month
    tick_dates = [display_data.iloc[i]['DATE'] for i in tick_positions if i < len(display_data)]
    tick_texts = [d.strftime('%b %Y') for d in tick_dates]

    # Calculate y-axis range
    y_min = display_data['ADJCLOSE'].min()
    y_max = display_data['ADJCLOSE'].max()
    y_range = y_max - y_min
    # Add 5% padding
    y_min -= y_range * 0.05
    y_max += y_range * 0.05

    fig.update_layout(
        title={
            'text': f"{symbol} - {'Upside' if breakout_type == 'high' else 'Downside'} Breakout",
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
            gridwidth=0.5,
            griddash='dot',
            dtick=21,
            tickmode='array',
            ticktext=tick_texts,
            tickvals=tick_positions,
            tickangle=-45,
            showline=True,
            linewidth=1,
            linecolor='#CCCCCC',
            zeroline=False
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#E5E5E5',
            gridwidth=0.5,
            griddash='dot',
            nticks=8,  # Limit number of ticks
            range=[y_min, y_max],  # Set range with padding
            showline=True,
            linewidth=1,
            linecolor='#CCCCCC',
            tickprefix='$',
            tickformat='.2f',
            zeroline=False
        )
    )
    return fig
    
def generate_analysis(ticker_data, symbol, breakout_type):
    current_row = ticker_data.iloc[0]
    signal_count = 0
    
    recent_data = ticker_data.head(21)
    
    if breakout_type == 'high':
        signal_count = recent_data['IS_ONE_MONTH_HIGH'].sum()
        price = current_row['ADJCLOSE']
        timeframe = "high" if current_row['IS_ONE_YEAR_HIGH'] else "1 month high"
        alert_type = "Upside"
    else:
        signal_count = recent_data['IS_ONE_MONTH_LOW'].sum()
        price = current_row['ADJCLOSE']
        timeframe = "low" if current_row['IS_ONE_YEAR_LOW'] else "1 month low"
        alert_type = "Downside"
    
    # Clean up description by:
    # 1. Replacing markdown special characters
    # 2. Ensuring no vertical text formatting
    # 3. Removing extra whitespace
    description = (current_row['DESCRIPTION']
                  .replace('_', '\\_')
                  .replace('*', '\\*')
                  .replace('\n', ' ')  # Replace newlines with spaces
                  .strip())  # Remove leading/trailing whitespace
    
    # Format the ordinal suffix properly
    if signal_count == 1:
        suffix = 'st'
    elif signal_count == 2:
        suffix = 'nd'
    elif signal_count == 3:
        suffix = 'rd'
    else:
        suffix = 'th'
    
    # Build the alert message with proper formatting
    alert = (
        f"**{alert_type} Breakout Alert:** {current_row['SHORTNAME']} ({symbol}) "
        f"just closed at a new {timeframe} of ${price:.2f}. {description} "
        f"This marks the {signal_count}{suffix} {alert_type.lower()} breakout signal "
        f"for {symbol} over the last 21 trading days."
    )
    
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
