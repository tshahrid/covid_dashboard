import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="General Overview", layout="wide")
st.title("Background on COVID-19")

st.info("""
    The COVID-19 pandemic was caused by **SARS-CoV-2**, a strain of coronavirus that 
    causes severe respiratory illness and in serious cases, death.
    The virus is spread by respiratory droplets and aerosols and has a high transmission rate, which was what accelerated its global spread.
    Below is a diagram showing how SARS-CoV-2 infects a human cell and proliferates.   """)

st.image("https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fs41579-020-00468-6/MediaObjects/41579_2020_468_Fig1_HTML.png?as=webp", caption="SARS-CoV-2 infection course. Source: Nature Reviews Microbiology")

st.subheader("Data Sources")
st.markdown("""
    The data in this dashboard is sourced from the **Johns Hopkins University Center for 
    Systems Science and Engineering (JHU CSSE)**, collected from **2020 to March 10, 2023**.
    """)

st.subheader("🔗 Useful Links")
col1, col2, col3 = st.columns(3)
with col1:
        st.link_button("Learn About COVID-19", "https://www.hopkinsguides.com/hopkins/view/Johns_Hopkins_ABX_Guide/540747/all/Coronavirus_COVID_19__SARS_CoV_2_")
with col2:
        st.link_button("WHO Live Dashboard", "https://www.who.int")
with col3:
        st.link_button("JHU Raw Data (GitHub)", "https://github.com/CSSEGISandData/COVID-19/blob/master/README.md")