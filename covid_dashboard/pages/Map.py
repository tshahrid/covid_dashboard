# Daily COVID information = confirmed cases, deaths and recovered individuals (3 dfs)
import pandas as pd
import requests as rq
import bs4
from io import StringIO
import streamlit as st
import plotly.express as px

## disclaimer I used Claude AI Sonnet 4.6 to help me write this code, but I edited many portions of the code to fit my own criteria

# Set up the page for app
st.set_page_config(page_title="COVID-19 Map", layout="wide")
st.title("COVID-19 World Maps")

# The code for loading and processing the data is wrapped in a function with caching to optimize performance
@st.cache_data
def load_data():

    # Load the 3 CSVs
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

    # Label each df
    cases["Type"]     = "Cases"
    deaths["Type"]    = "Deaths"
    recovered["Type"] = "Recovered"

    # Combine and switch to long format
    covid = pd.concat([cases, deaths, recovered])
    covid_long = covid.melt(
        id_vars=["Country/Region", "Lat", "Long", "Type"],
        var_name="Date",
        value_name="Count"
    )

    # Fix dates and add Year/Month columns
    covid_long["Date"]  = pd.to_datetime(covid_long["Date"], format="%m/%d/%y")
    covid_long["Year"]  = covid_long["Date"].dt.year.astype(str)
    covid_long["Month"] = covid_long["Date"].dt.strftime("%b")
    covid_long.rename(columns={"Country/Region": "Country/Territory"}, inplace=True)

    # Continent data scraping from Wikipedia
    REGION_URL = "https://simple.wikipedia.org/wiki/List_of_countries_by_continents"
    response   = rq.get(REGION_URL, headers={"User-Agent": "Chrome"})
    soup       = bs4.BeautifulSoup(response.text, "html.parser")
    tables     = soup.find_all("table", {"class": "wikitable"})

    continent_names   = ["Africa", "Asia", "Europe", "North America", "South America", "Oceania"]
    table_indices     = [0, 2, 3, 4, 5, 6]
    continent_dfs     = []

    for i, name in zip(table_indices, continent_names):
        df             = pd.read_html(StringIO(str(tables[i])))[0]
        df.columns     = df.columns.str.replace(r'\s*\[.*?\]', '', regex=True)
        df             = df.rename(columns={"English Name": "Country/Territory"})
        df["Continent"] = name
        continent_dfs.append(df[["Country/Territory", "Continent"]])

    continentdf = pd.concat(continent_dfs)

    # Merge continent into covid data
    covid_continent = pd.merge(covid_long, continentdf, on="Country/Territory", how="left")
    covid_continent.rename(columns={"Continent": "Region"}, inplace=True)

    # Manually fill in missing regions for countries not in the Wikipedia list
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

    # Drop rows with no region
    covid_continent = covid_continent.dropna(subset=["Region"])

    # Group by country to get total counts
    covid_total = covid_continent.groupby(
        ["Country/Territory", "Type", "Region", "Lat", "Long"], as_index=False
    )["Count"].sum()

    # Clean coordinates
    covid_total = covid_total.dropna(subset=["Lat", "Long"])
    covid_total["Lat"]   = pd.to_numeric(covid_total["Lat"],   errors="coerce")
    covid_total["Long"]  = pd.to_numeric(covid_total["Long"],  errors="coerce")

    # Clip negatives to 0 (data correction artifacts in recovered data)
    covid_total["Count"] = covid_total["Count"].clip(lower=0)

    return covid_total


# Load in data
covid_total = load_data()


# Making a filter that selects regions for the map
st.subheader("Filters")
region_filter = st.multiselect(
    "Filter by Region:",
    options=sorted(covid_total["Region"].unique()),
    default=sorted(covid_total["Region"].unique())
)

# ── Helper: build one map ────────────────────────────────────────
def build_map(type_label, color_sequence):

    filtered = covid_total[
        (covid_total["Type"]   == type_label) &
        (covid_total["Region"].isin(region_filter))
    ].copy()

    if filtered.empty:
        st.warning("No data available for the selected filters.")
        return

    # Main map
    fig = px.scatter_geo(
        filtered,
        lat="Lat",
        lon="Long",
        size="Count",
        color="Region",
        hover_name="Country/Territory",
        hover_data={"Count": True, "Region": True, "Lat": False, "Long": False},
        size_max=60,
        projection="natural earth",
        title=f"COVID-19 Total {type_label} by Country",
        color_discrete_sequence=color_sequence
    )
    fig.update_layout(
        height=600,
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        legend_title="Region"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Summary table with main data 
    st.divider()
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Countries", f"{filtered['Country/Territory'].nunique()}")
    col2.metric("Total Count",     f"{filtered['Count'].sum():,.0f}")
    col3.metric("Highest Country", filtered.loc[filtered["Count"].idxmax(), "Country/Territory"])

    # Raw data table
    with st.expander("Country Data Table"):
        st.dataframe(
            filtered[["Country/Territory", "Region", "Count"]]
            .sort_values("Count", ascending=False)
            .reset_index(drop=True),
            use_container_width=True
        )


# ── Tabs: one per map ────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["Cases", "Deaths", "Recovered"])

with tab1:
    build_map("Cases",     px.colors.qualitative.Plotly)

with tab2:
    build_map("Deaths",    px.colors.qualitative.Dark2)

with tab3:
    build_map("Recovered", px.colors.qualitative.Safe)