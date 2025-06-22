import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Levant Immunization Dashboard", layout="wide")

# ------------------ CONFIG ------------------
EXCEL_FILE = "wuenic2023rev_web-update.xlsx"

REGION_MAP = {
    'MENA': 'Middle East and North Africa',
    'ROSA': 'South Asia',
    'ESAR': 'Eastern and Southern Africa',
    'WCAR': 'West and Central Africa',
    'ECAR': 'Europe and Central Asia',
    'EAPR': 'East Asia and the Pacific',
    'LACR': 'Latin America and the Caribbean'
}

VACCINE_LABELS = {
    'BCG': 'Tuberculosis (BCG)',
    'DTP1': 'Diphtheria/Tetanus/Pertussis (1st)',
    'DTP3': 'Diphtheria/Tetanus/Pertussis (3rd)',
    'HEPB3': 'Hepatitis B (3rd)',
    'HEPBB': 'Hepatitis B (Birth)',
    'HIB3': 'Hib (Haemophilus influenzae type B)',
    'IPV1': 'Polio (IPV1)',
    'IPV2': 'Polio (IPV2)',
    'MCV1': 'Measles (1st)',
    'MCV2': 'Measles (2nd)',
    'MENGA': 'Meningococcal A',
    'PCV3': 'Pneumococcal (3rd)',
    'POL3': 'Polio (3rd)',
    'RCV1': 'Rubella',
    'ROTAC': 'Rotavirus',
    'YFV': 'Yellow Fever'
}

LEVANT_COUNTRIES = ['Iraq', 'Jordan', 'Lebanon', 'Palestine', 'Syria']

# ------------------ LOAD DATA ------------------
@st.cache_data
def load_data():
    if not os.path.exists(EXCEL_FILE):
        st.error(f"❌ File '{EXCEL_FILE}' not found.")
        st.stop()
    xls = pd.ExcelFile(EXCEL_FILE)
    sheets = [s for s in xls.sheet_names if s not in ['ReadMe', 'regional_global']]
    data = {}
    for sheet in sheets:
        df = xls.parse(sheet)
        df['region_full'] = df['unicef_region'].map(REGION_MAP).fillna('Other')
        data[sheet] = df
    return data

data = load_data()
sample_df = next(iter(data.values()))
years = sorted([int(col) for col in sample_df.columns if col.isdigit()])

# ------------------ SIDEBAR FILTERS ------------------
st.sidebar.title("🔧 Dashboard Filters")
selected_country = st.sidebar.selectbox("Select Country", LEVANT_COUNTRIES)
selected_vaccine = st.sidebar.selectbox("Select Vaccine", sorted(data.keys()), format_func=lambda x: VACCINE_LABELS.get(x, x))
selected_year = st.sidebar.selectbox("Select Year", sorted(years, reverse=True))

# Find Region
region_name = None
for df in data.values():
    row = df[df['country'] == selected_country]
    if not row.empty:
        region_name = row.iloc[0]['region_full']
        break

st.title("💉 Levant Immunization Dashboard")
st.markdown(f"**Country:** {selected_country} | **Vaccine:** {VACCINE_LABELS.get(selected_vaccine, selected_vaccine)} | **Year:** {selected_year} | **Region:** {region_name}")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Coverage Over Time")
    df_vax = data[selected_vaccine]
    country_data = df_vax[df_vax['country'] == selected_country]
    if not country_data.empty:
        ts = country_data.loc[:, country_data.columns.str.isnumeric()].T
        ts.columns = ['Coverage']
        ts.index.name = 'Year'
        ts = ts.dropna()
        st.line_chart(ts)

with col2:
    st.subheader("🗺️ Levant Coverage Map")
    map_df = data[selected_vaccine][data[selected_vaccine]['country'].isin(LEVANT_COUNTRIES)][['country', str(selected_year)]]
    map_df.columns = ['Country', 'Coverage']
    fig = px.choropleth(map_df,
        locations='Country',
        locationmode='country names',
        color='Coverage',
        color_continuous_scale='Viridis',
        range_color=(0, 100),
        scope='asia',
        title=f"{VACCINE_LABELS.get(selected_vaccine, selected_vaccine)} Coverage in {selected_year}"
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("📉 DTP Vaccine Dropout Rate")
if 'DTP1' in data and 'DTP3' in data:
    df1 = data['DTP1'][['country', str(selected_year)]]
    df3 = data['DTP3'][['country', str(selected_year)]]
    df_drop = df1.merge(df3, on='country', suffixes=('_DTP1', '_DTP3'))
    df_drop = df_drop[df_drop['country'].isin(LEVANT_COUNTRIES)]
    df_drop['Dropout Rate (%)'] = df_drop[f'{selected_year}_DTP1'] - df_drop[f'{selected_year}_DTP3']
    st.dataframe(df_drop.set_index('country'))