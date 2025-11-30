# app.py
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="🛒 Market Basket Dashboard", layout="wide")
st.title("🛒 Market Basket Analysis")
st.caption("Category-level associations — orders with ≥2 distinct categories")

# Load data
@st.cache_data
def load_data():
    return pd.read_csv("data/category_rules.csv")

try:
    df = load_data()
except:
    st.error("❌ File 'data/category_rules.csv' not found. Run your analysis script first.")
    st.stop()

# Sidebar filters
st.sidebar.header("FilterWhere")
min_lift = st.sidebar.slider("Min Lift", 1.0, 3.0, 1.5)
min_conf = st.sidebar.slider("Min Confidence", 0.0, 1.0, 0.3)

filtered = df[(df['lift'] >= min_lift) & (df['confidence'] >= min_conf)]

# KPIs
c1, c2, c3 = st.columns(3)
c1.metric("Total Rules", len(df))
c2.metric("Filtered", len(filtered))
c3.metric("Avg Lift", f"{filtered['lift'].mean():.2f}")

# Top rules bar chart
st.subheader("🔝 Top Rules by Lift")
top = filtered.nlargest(10, 'lift')
fig = px.bar(
    top, 
    x='lift', 
    y='antecedent', 
    color='confidence',
    orientation='h',
    hover_data=['consequent'],
    labels={'antecedent': 'Antecedent', 'lift': 'Lift'}
)
st.plotly_chart(fig, use_container_width=True)

# Table
st.subheader("📋 Rules Table")
st.dataframe(
    filtered.style.format({
        'support': '{:.2%}',
        'confidence': '{:.1%}',
        'lift': '{:.2f}'
    }),
    use_container_width=True,
    height=400
)

