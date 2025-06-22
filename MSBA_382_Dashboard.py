import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Levant Immunization Dashboard", layout="wide")
st.title("📊 Levant Region Immunization Dashboard")
st.markdown("Explore national vaccine coverage by country and year based on WHO/UNICEF 2023 data.")

# 📁 Excel file location
EXCEL_FILE = "C:/Users/yacou/Downloads/wuenic2023rev_web-update.xlsx"

# 🔍 Check if file exists
if not os.path.exists(EXCEL_FILE):
    st.error(f"❌ File '{EXCEL_FILE}' not found in the app directory.")
    st.stop()

# 🌍 UNICEF Region mapping
REGION_MAP = {
    'MENA': 'Middle East and North Africa',
    'ROSA': 'South Asia',
    'ESAR': 'Eastern and Southern Africa',
    'WCAR': 'West and Central Africa',
    'ECAR': 'Europe and Central Asia',
    'EAPR': 'East Asia and the Pacific',
    'LACR': 'Latin America and the Caribbean'
}

# 📥 Load Excel and cache it
@st.cache_data
def load_data():
    xls = pd.ExcelFile(EXCEL_FILE)
    sheets = [s for s in xls.sheet_names if s not in ['ReadMe', 'regional_global']]
    data = {}
    for sheet in sheets:
        df = xls.parse(sheet)
        df['region_full'] = df['unicef_region'].map(REGION_MAP).fillna('Other')
        data[sheet] = df
    return data

data = load_data()

# 🎯 Country and year selection
sample_df = next(iter(data.values()))
levant_countries = ['Iraq', 'Jordan', 'Lebanon', 'Palestine', 'Syria']
country = st.selectbox("Select a country", sorted(levant_countries))
year = st.selectbox("Select a year", sorted([int(col) for col in sample_df.columns if col.isdigit()], reverse=True))

# 🌐 Show region info
region_name = None
for df in data.values():
    row = df[df['country'] == country]
    if not row.empty:
        region_name = row.iloc[0]['region_full']
        break
if region_name:
    st.markdown(f"🌍 **UNICEF Region**: _{region_name}_")

# 📊 Vaccine coverage bar chart
coverage_dict = {}
for vaccine, df in data.items():
    value = df.loc[df['country'] == country, str(year)]
    if not value.empty:
        coverage_dict[vaccine] = float(value.values[0])
    else:
        coverage_dict[vaccine] = None

coverage_df = pd.DataFrame.from_dict(coverage_dict, orient='index', columns=['Coverage']).dropna()
coverage_df = coverage_df.sort_values('Coverage', ascending=False)

st.subheader(f"💉 Immunization Coverage in **{country}** ({year})")
st.bar_chart(coverage_df)

# 🔍 Raw data
with st.expander("📄 Show raw data"):
    st.dataframe(coverage_df.style.format("{:.1f}"))
