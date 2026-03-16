import pandas as pd
import requests as rq 
import bs4 
from io import StringIO
import streamlit as st
import plotly.express as px

## disclaimer I used Claude AI Sonnet 4.6 to help me write this code, but I edited many portions of the code to fit my own criteria

st.set_page_config(page_title="Main COVID-19 Trends", layout="wide")
st.title("Main COVID-19 Trends")

@st.cache_data
def load_data():

    cases = pd.read_csv(
        "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv",
        index_col=0
    )
    deaths = pd.read_csv(
        "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv",
        index_col=0
    )
    recovered = pd.read_csv(
        "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv",
        index_col=0
    )

    cases["Type"]     = "Cases"
    deaths["Type"]    = "Deaths"
    recovered["Type"] = "Recovered"

    covid = pd.concat([cases, deaths, recovered])
    covid_long = covid.melt(
        id_vars=["Country/Region", "Lat", "Long", "Type"],
        var_name="Date",
        value_name="Count"
    )

    covid_long["Date"]  = pd.to_datetime(covid_long["Date"], format="%m/%d/%y")
    covid_long["Year"]  = covid_long["Date"].dt.year.astype(str)
    covid_long["Month"] = covid_long["Date"].dt.strftime("%b")
    covid_long.rename(columns={"Country/Region": "Country/Territory"}, inplace=True)

    REGION_URL = "https://simple.wikipedia.org/wiki/List_of_countries_by_continents"
    response   = rq.get(REGION_URL, headers={"User-Agent": "Chrome"})
    soup       = bs4.BeautifulSoup(response.text, "html.parser")
    tables     = soup.find_all("table", {"class": "wikitable"})

    continent_names = ["Africa", "Asia", "Europe", "North America", "South America", "Oceania"]
    table_indices   = [0, 2, 3, 4, 5, 6]
    continent_dfs   = []

    for i, name in zip(table_indices, continent_names):
        df              = pd.read_html(StringIO(str(tables[i])))[0]
        df.columns      = df.columns.str.replace(r'\s*\[.*?\]', '', regex=True)
        df              = df.rename(columns={"English Name": "Country/Territory"})
        df["Continent"] = name
        continent_dfs.append(df[["Country/Territory", "Continent"]])

    continentdf = pd.concat(continent_dfs)

    covid_continent = pd.merge(covid_long, continentdf, on="Country/Territory", how="left")
    covid_continent.rename(columns={"Continent": "Region"}, inplace=True)

    continent_map = {
        'Albania': 'Europe',           'Antarctica': 'Antarctica',
        'Austria': 'Europe',           'Azerbaijan': 'Asia',
        'Bahamas': 'North America',    'Barbados': 'North America',
        'Belize': 'North America',     'Burma': 'Asia',
        'Cabo Verde': 'Africa',        'Canada': 'North America',
        'China': 'Asia',               'Congo (Brazzaville)': 'Africa',
        'Congo (Kinshasa)': 'Africa',  "Cote d'Ivoire": 'Africa',
        'Dominica': 'North America',   'El Salvador': 'North America',
        'Grenada': 'North America',    'Guatemala': 'North America',
        'Guinea': 'Africa',            'Haiti': 'North America',
        'Holy See': 'Europe',          'Honduras': 'North America',
        'Indonesia': 'Asia',           'Jamaica': 'North America',
        'Kazakhstan': 'Asia',          'Korea, North': 'Asia',
        'Korea, South': 'Asia',        'Mexico': 'North America',
        'Micronesia': 'Oceania',       'Moldova': 'Europe',
        'Nicaragua': 'North America',  'Panama': 'North America',
        'Saint Lucia': 'North America','Sao Tome and Principe': 'Africa',
        'Serbia': 'Europe',            'Taiwan*': 'Asia',
        'Timor-Leste': 'Asia',         'Turkey': 'Asia',
        'US': 'North America',         'Ukraine': 'Europe',
        'West Bank and Gaza': 'Asia'
    }

    covid_continent["Region"] = covid_continent["Region"].fillna(
        covid_continent["Country/Territory"].map(continent_map)
    )
    covid_continent = covid_continent.dropna(subset=["Region"])
    covid_continent["Count"] = covid_continent["Count"].clip(lower=0)

    return covid_continent


covid_long = load_data()

tab1, tab2, tab3, tab4 = st.tabs(["By Country", "By Region", "Compare Countries", "Daily Counts"])

# TAB 1 — Single country trend over time

with tab1:
    st.subheader("Trend for a Single Country")

    col1, col2 = st.columns(2)

    with col1:
        country = st.selectbox(
            "Select Country:",
            options=sorted(covid_long["Country/Territory"].unique()),
            index=sorted(covid_long["Country/Territory"].unique()).index("US")
            if "US" in covid_long["Country/Territory"].unique() else 0
        )
    with col2:
        metric = st.selectbox(
            "Select Metric:",
            options=["Cases", "Deaths", "Recovered"],
            key="tab1_metric"
        )

    # Filter
    df_country = covid_long[
        (covid_long["Country/Territory"] == country) &
        (covid_long["Type"] == metric)
    ].sort_values("Date")

    # Line chart
    fig1 = px.line(
        df_country,
        x="Date",
        y="Count",
        title=f"Cumulative {metric} in {country} Over Time",
        labels={"Count": metric, "Date": "Date"},
        color_discrete_sequence=["#e63946"]
    )
    fig1.update_traces(line=dict(width=2))
    fig1.update_layout(height=450, hovermode="x unified")
    st.plotly_chart(fig1, use_container_width=True)

    # Summary metrics
    st.divider()
    col1, col2, col3 = st.columns(3)
    col1.metric("Peak Count",    f"{df_country['Count'].max():,.0f}")
    col2.metric("Total by End",  f"{df_country['Count'].iloc[-1]:,.0f}" if not df_country.empty else "N/A")
    col3.metric("First Case",    str(df_country[df_country["Count"] > 0]["Date"].min().date()) if not df_country.empty else "N/A")

# TAB 2 — Region trend over time

with tab2:
    st.subheader("Trend by Region Over Time")

    col1, col2 = st.columns(2)

    with col1:
        metric2 = st.selectbox(
            "Select Metric:",
            options=["Cases", "Deaths", "Recovered"],
            key="tab2_metric"
        )
    with col2:
        view_by = st.radio(
            "View by:",
            options=["All Regions", "Select Regions"],
            horizontal=True
        )

    if view_by == "Select Regions":
        selected_regions = st.multiselect(
            "Select Regions:",
            options=sorted(covid_long["Region"].unique()),
            default=sorted(covid_long["Region"].unique())[:3]
        )
    else:
        selected_regions = sorted(covid_long["Region"].unique())

    # Group by region and date
    df_region = covid_long[
        (covid_long["Type"] == metric2) &
        (covid_long["Region"].isin(selected_regions))
    ].groupby(["Date", "Region"], as_index=False)["Count"].sum()

    fig2 = px.line(
        df_region,
        x="Date",
        y="Count",
        color="Region",
        title=f"Cumulative {metric2} by Region Over Time",
        labels={"Count": metric2, "Date": "Date"}
    )
    fig2.update_traces(line=dict(width=2))
    fig2.update_layout(height=450, hovermode="x unified")
    st.plotly_chart(fig2, use_container_width=True)


# TAB 3 — Compare multiple countries

with tab3:
    st.subheader("Compare Multiple Countries")

    col1, col2 = st.columns(2)

    with col1:
        compare_countries = st.multiselect(
            "Select Countries to Compare:",
            options=sorted(covid_long["Country/Territory"].unique()),
            default=["Malaysia", "US", "India", "Brazil"]
            if all(c in covid_long["Country/Territory"].unique()
                   for c in ["Malaysia", "US", "India", "Brazil"])
            else sorted(covid_long["Country/Territory"].unique())[:4]
        )
    with col2:
        metric3 = st.selectbox(
            "Select Metric:",
            options=["Cases", "Deaths", "Recovered"],
            key="tab3_metric"
        )

    if compare_countries:
        df_compare = covid_long[
            (covid_long["Country/Territory"].isin(compare_countries)) &
            (covid_long["Type"] == metric3)
        ].sort_values("Date")

        fig3 = px.line(
            df_compare,
            x="Date",
            y="Count",
            color="Country/Territory",
            title=f"Cumulative {metric3} — Country Comparison",
            labels={"Count": metric3, "Date": "Date", "Country/Territory": "Country"}
        )
        fig3.update_traces(line=dict(width=2))
        fig3.update_layout(height=450, hovermode="x unified")
        st.plotly_chart(fig3, use_container_width=True)

    else:
        st.info("Please select at least one country to compare.")


# TAB 4 — Daily Counts

with tab4:
    st.subheader("Daily Counts")

    col1, col2, col3 = st.columns(3)

    with col1:
        daily_country = st.selectbox(
            "Select Country:",
            options=sorted(covid_long["Country/Territory"].unique()),
            index=sorted(covid_long["Country/Territory"].unique()).index("US")
            if "US" in covid_long["Country/Territory"].unique() else 0,
            key="tab4_country"
        )
    with col2:
        daily_metric = st.selectbox(
            "Select Metric:",
            options=["Cases", "Deaths", "Recovered"],
            key="tab4_metric"
        )
    with col3:
        daily_year = st.selectbox(
            "Filter by Year:",
            options=["All"] + sorted(covid_long["Year"].unique()),
            key="tab4_year"
        )

    # Filter by country and metric
    df_daily = covid_long[
        (covid_long["Country/Territory"] == daily_country) &
        (covid_long["Type"] == daily_metric)
    ].sort_values("Date").copy()

    # Calculate daily new counts
    df_daily["Daily Count"] = df_daily["Count"].diff().clip(lower=0)

    # Apply year filter
    if daily_year != "All":
        df_daily = df_daily[df_daily["Year"] == daily_year]

    # Bar chart for daily counts
    fig_daily = px.bar(
        df_daily,
        x="Date",
        y="Daily Count",
        title=f"Daily New {daily_metric} in {daily_country}",
        labels={"Daily Count": f"Daily New {daily_metric}", "Date": "Date"},
        color_discrete_sequence=["#e63946"]
    )
    fig_daily.update_layout(height=450, hovermode="x unified")
    st.plotly_chart(fig_daily, use_container_width=True)

    # Summary metrics
    st.divider()
    col1, col2, col3 = st.columns(3)
    col1.metric("Peak Daily Count", f"{df_daily['Daily Count'].max():,.0f}")
    col2.metric("Average Daily Count", f"{df_daily['Daily Count'].mean():,.1f}")
    col3.metric("Peak Date", str(df_daily.loc[df_daily["Daily Count"].idxmax(), "Date"].date())
                if not df_daily.empty else "N/A")
