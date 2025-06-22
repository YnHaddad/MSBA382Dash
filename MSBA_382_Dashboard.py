
import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Global Immunization Dashboard", layout="wide")

# Reduce default font size and padding for compact layout
st.markdown("""
    <style>
    html, body, [class*="css"]  {
        font-size: 12px !important;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# ------------------ CONFIG ------------------
EXCEL_FILE = "wuenic2023rev_web-update.xlsx"

REGION_MAP = {
    'MENA': 'Middle East and North Africa', 'ROSA': 'South Asia', 'ESAR': 'Eastern and Southern Africa',
    'WCAR': 'West and Central Africa', 'ECAR': 'Europe and Central Asia',
    'EAPR': 'East Asia and the Pacific', 'LACR': 'Latin America and the Caribbean'
}

VACCINE_LABELS = {
    'BCG': 'Tuberculosis (BCG)', 'DTP1': 'Diphtheria/Tetanus/Pertussis (1st)', 'DTP3': 'Diphtheria/Tetanus/Pertussis (3rd)',
    'HEPB3': 'Hepatitis B (3rd)', 'HEPBB': 'Hepatitis B (Birth)', 'HIB3': 'Hib (Haemophilus influenzae type B)',
    'IPV1': 'Polio (IPV1)', 'IPV2': 'Polio (IPV2)', 'MCV1': 'Measles (1st)', 'MCV2': 'Measles (2nd)',
    'MENGA': 'Meningococcal A', 'PCV3': 'Pneumococcal (3rd)', 'POL3': 'Polio (3rd)',
    'RCV1': 'Rubella', 'ROTAC': 'Rotavirus', 'YFV': 'Yellow Fever'
}

COUNTRY_NAME_MAP = {
    'Syria': 'Syrian Arab Republic', 'Palestine': 'Palestinian Territory'
}

COLOR_SCALE_COVERAGE = 'RdYlGn'
COLOR_SCALE_DROPOUT = 'RdYlGn_r'

@st.cache_data
def load_data():
    if not os.path.exists(EXCEL_FILE):
        st.error(f"❌ File '{EXCEL_FILE}' not found.")
        st.stop()
    xls = pd.ExcelFile(EXCEL_FILE)
    sheets = [s for s in xls.sheet_names if s not in ['ReadMe', 'regional_global']]
    data = {sheet: xls.parse(sheet).assign(region_full=lambda df: df['unicef_region'].map(REGION_MAP).fillna('Other')) for sheet in sheets}
    return data

data = load_data()
sample_df = next(iter(data.values()))
years = sorted([int(col) for col in sample_df.columns if col.isnumeric()])
all_countries = set()
for df in data.values():
    all_countries.update(df['country'].dropna().unique())
countries = sorted(all_countries)

st.title("🌍 Global Child Immunization Performance (2000–2023)")
col_country, col_vaccine, col_year = st.columns([1.5, 2, 1.2])
with col_country:
    selected_country = st.selectbox("Country", countries)
with col_vaccine:
    selected_vaccine = st.selectbox("Vaccine", sorted(data.keys()), format_func=lambda x: VACCINE_LABELS.get(x, x))
with col_year:
    selected_year = st.selectbox("Year", sorted(years, reverse=True))

region_name = None
for df in data.values():
    row = df[df['country'] == selected_country]
    if not row.empty:
        region_name = row.iloc[0]['region_full']
        break

st.markdown(f"**Country:** {selected_country} | **Vaccine:** {VACCINE_LABELS.get(selected_vaccine, selected_vaccine)} | **Year:** {selected_year} | **Region:** {region_name}")

metric_df = data[selected_vaccine][['country', str(selected_year)]].dropna()
metric_df.columns = ['country', 'coverage']
if not metric_df.empty:
    highest_row = metric_df.loc[metric_df['coverage'].idxmax()]
    lowest_row = metric_df.loc[metric_df['coverage'].idxmin()]
    col_high, col_low = st.columns(2)
    with col_high:
        st.metric(label="📈 Highest Coverage", value=f"{highest_row['country']} ({highest_row['coverage']}%)")
    with col_low:
        st.metric(label="📉 Lowest Coverage", value=f"{lowest_row['country']} ({lowest_row['coverage']}%)")

col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("📊 Coverage Over Time")
    df_vax = data[selected_vaccine]
    country_data = df_vax[df_vax['country'] == selected_country]
    if not country_data.empty:
        ts = country_data.loc[:, country_data.columns.str.isnumeric()].T
        ts.columns = ['Coverage']
        ts.index.name = 'Year'
        ts = ts.dropna()
        st.line_chart(ts, use_container_width=True, height=280)

with col2:
    st.subheader("🗺️ Global Coverage Map")
    map_df = data[selected_vaccine][['country', str(selected_year)]]
    map_df['Country'] = map_df['country'].replace(COUNTRY_NAME_MAP).fillna(map_df['country'])
    map_df = map_df[['Country', str(selected_year)]].rename(columns={str(selected_year): 'Coverage'})
    fig = px.choropleth(
        map_df,
        locations='Country',
        locationmode='country names',
        color='Coverage',
        color_continuous_scale=COLOR_SCALE_COVERAGE,
        range_color=(0, 100),
        title=f"{VACCINE_LABELS.get(selected_vaccine, selected_vaccine)} Coverage in {selected_year}",
        hover_name='Country',
        labels={'Coverage': 'Coverage (%)'}
    )
    fig.update_geos(
        projection_type='robinson',
        showcountries=True,
        showcoastlines=False,
        showframe=False,
        lonaxis_range=[-180, 180],
        lataxis_range=[-60, 85]
    )
    
fig.update_layout(
    font=dict(size=10, color='white'),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    geo_bgcolor='rgba(0,0,0,0)',
    margin=dict(l=10, r=10, t=30, b=0),
    height=300
)
,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        geo_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=10, t=30, b=0),
        height=300
    )
    fig.update_traces(marker_line_width=0.2)
    st.plotly_chart(fig, use_container_width=True)

with st.expander("🧮 Vaccine Scorecard & Dropout Insights", expanded=True):
    col_scorecard, col_dropout = st.columns(2)

    with col_scorecard:
        st.markdown(f"<h4 style='color:#FFD700; font-weight:bold;'>📋 {selected_country} Vaccine Scorecard vs Global Average ({selected_year})</h4>", unsafe_allow_html=True)
        scorecard = []
        for vac in data.keys():
            df = data[vac][['country', str(selected_year)]].dropna()
            country_val = df[df['country'] == selected_country][str(selected_year)].values
            if len(country_val) == 0:
                continue
            global_avg = df[str(selected_year)].mean()
            scorecard.append({
                'Vaccine': VACCINE_LABELS.get(vac, vac),
                selected_country: round(country_val[0], 1),
                'Global Avg': round(global_avg, 1)
            })
        scorecard_df = pd.DataFrame(scorecard).sort_values(by='Global Avg', ascending=False)
        styled_df = scorecard_df.set_index('Vaccine').style.set_properties(
            **{
                'font-size': '14px',
                'font-weight': 'bold',
                'color': 'black',
                'background-color': '#ffffff',
                'border-color': '#444444'
            }
        )
        st.dataframe(styled_df, use_container_width=True, height=250)

    with col_dropout:
        if 'DTP1' in data and 'DTP3' in data:
            df1 = data['DTP1'][['country', str(selected_year)]].rename(columns={str(selected_year): 'DTP1'})
            df3 = data['DTP3'][['country', str(selected_year)]].rename(columns={str(selected_year): 'DTP3'})
            df_drop = df1.merge(df3, on='country').dropna()
            df_drop['Dropout Rate (%)'] = ((df_drop['DTP1'] - df_drop['DTP3']) / df_drop['DTP1']) * 100
            df_drop = df_drop[df_drop['Dropout Rate (%)'].between(-100, 100)]
            dropout_fig = px.bar(
                df_drop, x='country', y='Dropout Rate (%)', color='Dropout Rate (%)',
                color_continuous_scale=COLOR_SCALE_DROPOUT,
                title=f"DTP1 to DTP3 Dropout Rate in {selected_year}"
            )
            dropout_
fig.update_layout(
    font=dict(size=10, color='white'),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    geo_bgcolor='rgba(0,0,0,0)',
    margin=dict(l=10, r=10, t=30, b=0),
    height=300
)
)
            st.plotly_chart(dropout_fig, use_container_width=True)
