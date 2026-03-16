import streamlit as st

st.set_page_config(
    page_title="COVID-19 Dashboard",
    page_icon="🦠",
    layout="wide"
)

st.title("COVID-19 Global Dashboard")
st.markdown("""
## Welcome to the COVID-19 Dashboard for data from 2020 - 2023. Use the **sidebar** to navigate between pages:

- **Overview** — Information about COVID-19 and the data used in this dashboard
- **World Map** — Interactive world map
- **Trends** — Country-level time series charts
""")