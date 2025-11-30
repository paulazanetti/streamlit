# app.py — E-Commerce Dashboard (Fixed Filters)
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# =============== DATA PREP ===============
@st.cache_data
def load_and_prepare_data():
    # 🔁 Load your df_delivered
    df = pd.read_csv("df_delivered.csv")

    # Ensure numeric/year/month are int (in case read as float)
    df['year'] = df['year'].astype(int)
    df['month'] = df['month'].astype(int)

    # Create 'revenue' = price + freight
    df['revenue'] = df['price'] + df['freight_value']

    # Create 'period' as 'YYYY-MM' for filtering/display
    df['period'] = df['year'].astype(str) + '-' + df['month'].astype(str).str.zfill(2)

    return df

df = load_and_prepare_data()

# =============== SIDEBAR FILTERS ===============
st.sidebar.header("FilterWhere")

# --- Date Filter: Year & Month (not datetime) ---
years = sorted(df['year'].unique())
months = list(range(1, 13))

selected_year = st.sidebar.multiselect("Year", years, default=years)
selected_month = st.sidebar.multiselect("Month", months, default=months)

# --- State Filter: if empty → show all ---
states = sorted(df['customer_state'].dropna().unique())
selected_states = st.sidebar.multiselect("State", states, default=[])

# --- Category Filter ---
categories = sorted(df['product_category_name_english'].dropna().unique())
selected_categories = st.sidebar.multiselect("Category", categories, default=[])

# Apply filters
filtered = df.copy()

# Year/Month
if selected_year:
    filtered = filtered[filtered['year'].isin(selected_year)]
if selected_month:
    filtered = filtered[filtered['month'].isin(selected_month)]

# State: only apply if selection is NOT empty
if selected_states:
    filtered = filtered[filtered['customer_state'].isin(selected_states)]

# Category: only apply if selection is NOT empty
if selected_categories:
    filtered = filtered[filtered['product_category_name_english'].isin(selected_categories)]

# Handle empty result
if filtered.empty:
    st.warning("No data matches the current filters.")
    st.stop()

# =============== METRICS ===============
st.set_page_config(page_title="🛒 E-Commerce Dashboard", layout="wide")
st.title("🛒 E-Commerce Performance Dashboard")
st.markdown("Insights from delivered orders — Olist Brazil")

# KPIs
total_revenue = filtered['revenue'].sum()
total_orders = len(filtered)
aov = total_revenue / total_orders if total_orders > 0 else 0
avg_rating = filtered['review_score'].mean()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"R$ {total_revenue:,.0f}")
col2.metric("Orders", f"{total_orders:,}")
col3.metric("Avg Order Value", f"R$ {aov:.0f}")
col4.metric("Avg Rating", f"{avg_rating:.1f} ⭐")

st.markdown("---")

# =============== CHART 1: Monthly Sales & Orders ===============
st.subheader("📈 Monthly Sales & Orders")

monthly = filtered.groupby('period').agg({
    'revenue': 'sum',
    'order_id': 'nunique'
}).reset_index().rename(columns={'order_id': 'orders'})

# Sort by period (YYYY-MM)
monthly = monthly.sort_values('period')

fig1 = go.Figure()

fig1.add_trace(go.Bar(
    x=monthly['period'],
    y=monthly['revenue'],
    name='Revenue (R$)',
    yaxis='y',
    marker_color='#FF6B6B'
))

fig1.add_trace(go.Scatter(
    x=monthly['period'],
    y=monthly['orders'],
    name='Orders',
    yaxis='y2',
    mode='lines+markers',
    line=dict(color='#4ECDC4', width=3)
))

fig1.update_layout(
    yaxis=dict(title="Revenue (R$)", side="left"),
    yaxis2=dict(title="Orders", side="right", overlaying="y", showgrid=False),
    xaxis_title="Period (YYYY-MM)",
    xaxis_tickangle=-45,
    legend=dict(x=0.01, y=0.99)
)
st.plotly_chart(fig1, use_container_width=True)

# =============== CHART 2: Sales by State ===============
st.subheader("📍 Sales by State")

state_sales = filtered.groupby('customer_state').agg({
    'revenue': 'sum',
    'order_id': 'nunique'
}).reset_index().sort_values('revenue', ascending=False)

fig2 = px.bar(
    state_sales,
    x='customer_state',
    y='revenue',
    color='revenue',
    color_continuous_scale='Blues',
    labels={'customer_state': 'State', 'revenue': 'Revenue (R$)'},
    text='revenue'
)
fig2.update_traces(texttemplate='R$%{text:,.0f}', textposition='outside')
fig2.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig2, use_container_width=True)

# =============== CHART 3: Top 10 Categories ===============
st.subheader("📦 Top 10 Categories by Revenue")

cat_sales = filtered.groupby('product_category_name_english').agg({
    'revenue': 'sum',
    'order_id': 'nunique'
}).reset_index().nlargest(10, 'revenue')

fig3 = px.bar(
    cat_sales,
    x='revenue',
    y='product_category_name_english',
    orientation='h',
    color='revenue',
    color_continuous_scale='Viridis',
    labels={'product_category_name_english': 'Category', 'revenue': 'Revenue (R$)'}
)
fig3.update_layout(yaxis={'categoryorder': 'total ascending'})
st.plotly_chart(fig3, use_container_width=True)

# =============== CHART 4: Rating vs Revenue ===============
st.subheader("⭐ Avg Rating vs Revenue by Category")

cat_metrics = filtered.groupby('product_category_name_english').agg({
    'revenue': 'sum',
    'review_score': 'mean',
    'order_id': 'nunique'
}).reset_index()

# Only show categories with ≥10 orders (statistically stable)
cat_metrics = cat_metrics[cat_metrics['order_id'] >= 10]

if not cat_metrics.empty:
    fig4 = px.scatter(
        cat_metrics,
        x='review_score',
        y='revenue',
        size='order_id',
        color='revenue',
        hover_name='product_category_name_english',
        size_max=60,
        labels={
            'review_score': 'Avg Review Score',
            'revenue': 'Total Revenue (R$)',
            'order_id': 'Orders'
        },
        title="High Revenue + High Rating = 🏆 Ideal Categories"
    )
    fig4.add_vline(x=4.0, line_dash="dash", line_color="red", annotation_text="4.0")
    st.plotly_chart(fig4, use_container_width=True)
else:
    st.info("No category has ≥10 orders with current filters.")