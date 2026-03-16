# Daily COVID information = confirmed cases, deaths and recovered individuals (3 dfs)
# Country of choice = Malaysia

# dfs from github I need to get this data from are:
## time_series_covid19_confirmed_global.csv
## time_series_covid19_deaths_global.csv
## time_series_covid19_recovered_global.csv

# obtain the dfs

import pandas as pd

cases = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv"
cases = pd.read_csv(cases, index_col=0)

deaths = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv"
deaths = pd.read_csv(deaths, index_col=0)

recovered = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv"
recovered = pd.read_csv(recovered, index_col=0)

# make new columns defining the type of data

cases["Type"] = "Cases"
deaths["Type"] = "Deaths"
recovered["Type"] = "Recovered"

#concat

covid = pd.concat([cases, deaths, recovered])

# go from wide to long format
covid_long = covid.melt(
    id_vars=["Country/Region", "Lat", "Long", "Type"],
    var_name="Date",
    value_name="Count"
)

covid_long["Date"] = pd.to_datetime(covid_long["Date"], format="%m/%d/%y")

covid_long["Year"] = covid_long["Date"].dt.year.astype(str)
covid_long["Month"] = covid_long["Date"].dt.strftime("%b")  
covid_long.rename(columns={"Country/Region": "Country/Territory"}, inplace=True)

# okay so at this point you probably want to group countries by region I guess
import requests as rq
import bs4
import pandas as pd
from io import StringIO

REGION_URL = "https://simple.wikipedia.org/wiki/List_of_countries_by_continents"

region = rq.get(REGION_URL, headers={"User-Agent": "Chrome"})
regionbs4 = bs4.BeautifulSoup(region.text, 'html.parser')
tables = regionbs4.find_all("table", {"class": "wikitable"})

africa = pd.read_html(StringIO(str(tables[0])))[0]
asia = pd.read_html(StringIO(str(tables[2])))[0]
euro = pd.read_html(StringIO(str(tables[3])))[0]
north_america = pd.read_html(StringIO(str(tables[4])))[0]
south_america = pd.read_html(StringIO(str(tables[5])))[0]
oceania = pd.read_html(StringIO(str(tables[6])))[0]

africa["Continent"] = "Africa"
asia["Continent"] = "Asia"
euro["Continent"] = "Europe"
north_america["Continent"] = "North America"
south_america["Continent"] = "South America"
oceania["Continent"] = "Oceania"

# remove extra stuff in brackets from English Name in order to rename

africa.columns = africa.columns.str.replace(r'\s*\[.*?\]', '', regex=True)
asia.columns = asia.columns.str.replace(r'\s*\[.*?\]', '', regex=True)
euro.columns = euro.columns.str.replace(r'\s*\[.*?\]', '', regex=True)
north_america.columns = north_america.columns.str.replace(r'\s*\[.*?\]', '', regex=True)
south_america.columns = south_america.columns.str.replace(r'\s*\[.*?\]', '', regex=True)
oceania.columns = oceania.columns.str.replace(r'\s*\[.*?\]', '', regex=True)

#change colname from english name to Country/Territory

africa = africa.rename(columns={"English Name": "Country/Territory"})
asia = asia.rename(columns={"English Name": "Country/Territory"})
euro = euro.rename(columns={"English Name": "Country/Territory"})
north_america = north_america.rename(columns={"English Name": "Country/Territory"})
south_america = south_america.rename(columns={"English Name": "Country/Territory"})
oceania = oceania.rename(columns={"English Name": "Country/Territory"})

africa = africa[['Country/Territory','Continent']]
asia = asia[['Country/Territory','Continent']]
euro = euro[['Country/Territory','Continent']]
north_america = north_america[['Country/Territory','Continent']]
south_america = south_america[['Country/Territory','Continent']]
oceania = oceania[['Country/Territory','Continent']]
continentdf = pd.concat([africa, asia, euro, north_america, south_america, oceania])

# merge covid cases with continent

covid_continent = pd.merge(covid_long, continentdf, on="Country/Territory", how="left")

#rename continent to region

covid_continent.rename(columns={"Continent": "Region"}, inplace=True)

covid_continent[covid_continent['Region'].isna()]['Country/Territory'].nunique()
covid_continent.loc[covid_continent['Region'].isna(), 'Country/Territory'].unique()

# adding region to NaNs

continent_map = {
    'Albania': 'Europe',
    'Antarctica': 'Antarctica',
    'Austria': 'Europe',
    'Azerbaijan': 'Asia',
    'Bahamas': 'North America',
    'Barbados': 'North America',
    'Belize': 'North America',
    'Burma': 'Asia',
    'Cabo Verde': 'Africa',
    'Canada': 'North America',
    'China': 'Asia',
    'Congo (Brazzaville)': 'Africa',
    'Congo (Kinshasa)': 'Africa',
    'Costa Rica': 'North America',
    "Cote d'Ivoire": 'Africa',
    'Dominica': 'North America',
    'El Salvador': 'North America',
    'Grenada': 'North America',
    'Guatemala': 'North America',
    'Guinea': 'Africa',
    'Haiti': 'North America',
    'Holy See': 'Europe',
    'Honduras': 'North America',
    'Indonesia': 'Asia',
    'Jamaica': 'North America',
    'Kazakhstan': 'Asia',
    'Korea, North': 'Asia',
    'Korea, South': 'Asia',
    'Mexico': 'North America',
    'Micronesia': 'Oceania',
    'Moldova': 'Europe',
    'Nicaragua': 'North America',
    'Panama': 'North America',
    'Saint Lucia': 'North America',
    'Sao Tome and Principe': 'Africa',
    'Serbia': 'Europe',
    'Taiwan*': 'Asia',
    'Timor-Leste': 'Asia',
    'Turkey': 'Asia',
    'US': 'North America',
    'Ukraine': 'Europe',
    'West Bank and Gaza': 'Asia'
}

covid_continent['Region'] = covid_continent['Region'].fillna(covid_continent['Country/Territory'].map(continent_map))

covid_continent[covid_continent['Region'].isna()]['Country/Territory'].unique()

covid_continent = covid_continent.dropna(subset=['Region'])

covid_continent['Region'].isna().sum()

#make a new df that has total counts for each country/territory and type

covid_total = covid_continent.groupby(["Country/Territory", "Type", "Region", "Lat", "Long"], as_index=False)["Count"].sum()

#make a df for only the cases so i can build a map

covid_total_cases = covid_total[covid_total["Type"] == "Cases"]

covid_total_cases = covid_continent.dropna(subset=["Lat", "Long"])
#make sure coordinates are numeric
covid_total_cases["Lat"] = pd.to_numeric(covid_total_cases["Lat"], errors="coerce")
covid_total_cases["Long"] = pd.to_numeric(covid_total_cases["Long"], errors="coerce")

############################################################ Creating the Dashboard in Streamlit ############################################################
# Main page

import folium 
import streamlit as st
from streamlit_folium import st_folium



