# app.py — E-Commerce Dashboard for df_delivered
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# =============== DATA PREP ===============
@st.cache_data
def load_and_prepare_data():
    # 🔁 Assuming df_delivered is loaded (adjust path as needed)
    df = pd.read_csv("df_delivered.csv")  # <-- seu arquivo

    # Ensure datetime
    df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])

    # Create 'revenue' = price + freight (gross revenue)
    df['revenue'] = df['price'] + df['freight_value']

    # Optional: Create month-year for grouping
    df['order_month'] = df['order_purchase_timestamp'].dt.to_period('M').astype(str)

    return df

df = load_and_prepare_data()

# =============== SIDEBAR FILTERS ===============
st.sidebar.header("FilterWhere")

# Date range
min_date = df['order_purchase_timestamp'].min().date()
max_date = df['order_purchase_timestamp'].max().date()
start_date, end_date = st.sidebar.date_input(
    "Order Date Range",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# States
states = sorted(df['customer_state'].dropna().unique())
selected_states = st.sidebar.multiselect("States", states, default=states)

# Categories
categories = sorted(df['product_category_name_english'].dropna().unique())
selected_categories = st.sidebar.multiselect("Categories", categories, default=[])

# Apply filters
filtered = df[
    (df['order_purchase_timestamp'].dt.date >= start_date) &
    (df['order_purchase_timestamp'].dt.date <= end_date) &
    (df['customer_state'].isin(selected_states))
]

if selected_categories:
    filtered = filtered[filtered['product_category_name_english'].isin(selected_categories)]

# Fallback if no data
if filtered.empty:
    st.warning("No data matches the filters.")
    st.stop()

# =============== METRICS ===============
st.set_page_config(page_title="🛒 E-Commerce Dashboard", layout="wide")
st.title("🛒 E-Commerce Performance Dashboard")
st.markdown("Insights from delivered orders — Olist Brazil")

# KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"R$ {filtered['revenue'].sum():,.0f}")
col2.metric("Orders", f"{len(filtered):,}")
col3.metric("Avg Order Value", f"R$ {filtered['revenue'].mean():.0f}")
col4.metric("Avg Rating", f"{filtered['review_score'].mean():.1f} ⭐")

st.markdown("---")

# =============== CHART 1: Monthly Sales & Orders ===============
st.subheader("📈 Monthly Sales & Orders")

monthly = filtered.groupby('order_month').agg({
    'revenue': 'sum',
    'order_id': 'nunique'
}).reset_index().rename(columns={'order_id': 'orders'})

fig1 = go.Figure()

fig1.add_trace(go.Bar(
    x=monthly['order_month'],
    y=monthly['revenue'],
    name='Revenue (R$)',
    yaxis='y',
    marker_color='#FF6B6B'
))

fig1.add_trace(go.Scatter(
    x=monthly['order_month'],
    y=monthly['orders'],
    name='Orders',
    yaxis='y2',
    mode='lines+markers',
    line=dict(color='#4ECDC4', width=3)
))

fig1.update_layout(
    yaxis=dict(title="Revenue (R$)", side="left"),
    yaxis2=dict(title="Orders", side="right", overlaying="y", showgrid=False),
    xaxis_title="Month",
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

# =============== CHART 3: Top 10 Categories by Revenue ===============
st.subheader("📦 Top 10 Categories by Revenue")

cat_sales = filtered.groupby('product_category_name_english').agg({
    'revenue': 'sum',
    'order_id': 'nunique'
}).reset_index().nlargest(10, 'revenue')

fig3 = px.treemap(
    cat_sales,
    path=['product_category_name_english'],
    values='revenue',
    color='revenue',
    color_continuous_scale='Viridis',
    labels={'product_category_name_english': 'Category', 'revenue': 'Revenue'}
)
st.plotly_chart(fig3, use_container_width=True)

# =============== CHART 4: Avg Rating vs Revenue per Category ===============
st.subheader("⭐ Rating vs Revenue by Category")

cat_metrics = filtered.groupby('product_category_name_english').agg({
    'revenue': 'sum',
    'review_score': 'mean',
    'order_id': 'nunique'
}).reset_index()
cat_metrics = cat_metrics[cat_metrics['order_id'] >= 10]  # stable categories

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
fig4.add_vline(x=4.0, line_dash="dash", line_color="red", annotation_text="4.0 Threshold")
st.plotly_chart(fig4, use_container_width=True)

# =============== BONUS: Freight Analysis ===============
with st.expander("📦 Freight Cost Insights (Bonus)"):
    st.write("Freight as % of product price — key for margin analysis")
    
    filtered['freight_ratio'] = filtered['freight_value'] / filtered['price']
    
    fig5 = px.scatter(
        filtered.sample(min(5000, len(filtered))),  # sample to avoid overload
        x='price',
        y='freight_value',
        color='freight_ratio',
        size='revenue',
        hover_data=['product_category_name_english'],
        labels={'price': 'Product Price (R$)', 'freight_value': 'Freight (R$)'},
        color_continuous_scale='RdYlBu_r',
        title="Freight vs Product Price"
    )
    st.plotly_chart(fig5, use_container_width=True)
    
    st.metric(
        "Avg Freight Ratio",
        f"{filtered['freight_ratio'].mean():.1%}",
        help="Average freight cost as % of product price"
    )