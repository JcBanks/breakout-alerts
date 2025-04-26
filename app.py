import streamlit as st

# Set page configuration
st.set_page_config(
    page_title="Project Blizzard Dashboard",
    layout="wide",
    page_icon="📊",
)

# Initialize session state for the view if it doesn't exist
if 'view' not in st.session_state:
    st.session_state.view = 'main'

# Main dashboard layout
def show_main_page():
    st.title("Breakout Monitor Dashboard")
    st.markdown("Welcome to the Project Blizzard Dashboard! Choose one of the monitors below:")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("ETF Breakout Monitor"):
            st.session_state.view = 'etf'

    with col2:
        if st.button("Growth Stock Monitor"):
            st.session_state.view = 'growth'

    with col3:
        if st.button("Single Stock Chart"):
            st.session_state.view = 'single'

# ETF Breakout Monitor page
def show_etf_breakout_monitor():
    st.title("ETF Breakout Monitor")
    st.write("This is where your ETF breakout magic happens. ✨📈")
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.view = 'main'

# Growth Stock Monitor page
def show_growth_stock_monitor():
    st.title("Growth Stock Monitor")
    st.write("Welcome to the jungle — where the growth stocks run wild. 🌱📊")
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.view = 'main'

# Single Stock Chart page
def show_single_stock_chart():
    st.title("Single Stock Chart")
    st.write("Zoom into the action on one lonely stock... but make it beautiful. 🎯📉")
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.view = 'main'

# Router based on the current view
def render_page():
    if st.session_state.view == 'main':
        show_main_page()
    elif st.session_state.view == 'etf':
        show_etf_breakout_monitor()
    elif st.session_state.view == 'growth':
        show_growth_stock_monitor()
    elif st.session_state.view == 'single':
        show_single_stock_chart()
    else:
        st.error("Unknown page! Taking you back to safety. 🛟")
        st.session_state.view = 'main'
        show_main_page()

# Actually run the page
render_page()
