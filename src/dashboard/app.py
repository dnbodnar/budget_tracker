import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text

st.set_page_config(
    page_title="Budget Tracker",
    page_icon="💰",
    layout="wide"
)

# Database connection settings
db_host = "localhost"
db_port = "5432"
db_name = "budget_tracker"
db_user = "budget_user"
db_password = "budget_pass"

@st.cache_resource
def get_engine():
    connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    return create_engine(connection_string)

@st.cache_data(ttl=300)
def load_category_summary():
    engine = get_engine()
    return pd.read_sql("SELECT * FROM gold.category_summary", engine)

@st.cache_data(ttl=300)
def load_monthly_totals():
    engine = get_engine()
    return pd.read_sql("SELECT * FROM gold.monthly_totals ORDER BY month", engine)

@st.cache_data(ttl=300)
def load_monthly_by_category():
    engine = get_engine()
    return pd.read_sql("SELECT * FROM gold.monthly_spending_by_category ORDER BY month", engine)

@st.cache_data(ttl=300)
def load_top_merchants():
    engine = get_engine()
    return pd.read_sql("SELECT * FROM gold.top_merchants LIMIT 20", engine)

@st.cache_data(ttl=300)
def load_card_stats():
    engine = get_engine()
    return pd.read_sql("SELECT * FROM gold.card_usage_stats", engine)

@st.cache_data(ttl=300)
def load_available_years():
    engine = get_engine()
    return pd.read_sql(
        "SELECT DISTINCT EXTRACT(year FROM transaction_date)::int AS year FROM silver.transactions ORDER BY year DESC",
        engine
    )["year"].tolist()

@st.cache_data(ttl=300)
def load_available_months(year):
    engine = get_engine()
    return pd.read_sql(f"""
        SELECT DISTINCT EXTRACT(month FROM transaction_date)::int AS month_num,
               TO_CHAR(transaction_date, 'Mon') AS month_name
        FROM silver.transactions
        WHERE EXTRACT(year FROM transaction_date) = {year}
        ORDER BY month_num
    """, engine)

@st.cache_data(ttl=300)
def load_category_filtered(year, month_nums):
    engine = get_engine()
    month_filter = f"AND EXTRACT(month FROM transaction_date) IN ({','.join(str(m) for m in month_nums)})" if month_nums else ""
    base_filter = f"EXTRACT(year FROM transaction_date) = {year} {month_filter}"
    return pd.read_sql(f"""
        SELECT
            category,
            COUNT(*) AS transaction_count,
            SUM(amount) AS total_spent,
            ROUND(100.0 * SUM(amount) / (SELECT SUM(amount) FROM silver.transactions WHERE {base_filter}), 2) AS percent_of_total
        FROM silver.transactions
        WHERE {base_filter}
        GROUP BY category
        ORDER BY total_spent DESC
    """, engine)

@st.cache_data(ttl=300)
def load_summary_stats():
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT
                COUNT(*) as total_transactions,
                SUM(amount) as total_spent,
                COUNT(DISTINCT merchant_name) as unique_merchants,
                MIN(transaction_date) as earliest,
                MAX(transaction_date) as latest
            FROM silver.transactions
        """))
        return result.fetchone()

st.title("💰 Budget Tracker")
st.caption("Personal spending dashboard powered by Gmail transaction data")

stats = load_summary_stats()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Spent", f"${stats[1]:,.2f}")
with col2:
    st.metric("Transactions", f"{stats[0]:,}")
with col3:
    st.metric("Unique Merchants", f"{stats[2]:,}")
with col4:
    st.metric("Date Range", f"{stats[3]} → {stats[4]}")

st.divider()

tab1, tab2, tab3, tab4 = st.tabs(["Categories", "Monthly Trends", "Top Merchants", "Cards"])

with tab1:
    available_years = load_available_years()
    selected_year = st.selectbox("Year", available_years, index=0)

    months_df = load_available_months(selected_year)
    month_options = months_df["month_name"].tolist()
    selected_month_names = st.multiselect("Month (optional)", month_options)

    # map selected month names back to numbers for the query
    month_map = dict(zip(months_df["month_name"], months_df["month_num"]))
    selected_month_nums = [month_map[m] for m in selected_month_names]

    if selected_month_names:
        label = f"{selected_year} - {', '.join(selected_month_names)}"
    else:
        label = str(selected_year)

    st.subheader(f"Spending by Category - {label}")

    category_df = load_category_filtered(selected_year, selected_month_nums)

    col1, col2 = st.columns([2, 1])

    with col1:
        fig = px.bar(
            category_df,
            x="total_spent",
            y="category",
            orientation="h",
            color="category",
            text=category_df["total_spent"].apply(lambda x: f"${x:,.0f}"),
            labels={"total_spent": "Total Spent ($)", "category": "Category"},
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(showlegend=False, yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, width='stretch')

    with col2:
        display_df = category_df[["category", "total_spent", "transaction_count", "percent_of_total"]].copy()
        display_df.columns = ["Category", "Total ($)", "Transactions", "% of Total"]
        display_df["Total ($)"] = display_df["Total ($)"].apply(lambda x: f"${x:,.2f}")
        display_df["% of Total"] = display_df["% of Total"].apply(lambda x: f"{x:.1f}%")
        st.dataframe(display_df, hide_index=True, width='stretch')

with tab2:
    st.subheader("Monthly Spending Trends")

    monthly_df = load_monthly_totals()
    monthly_df["month"] = pd.to_datetime(monthly_df["month"]).dt.strftime("%Y-%m")

    fig = px.line(
        monthly_df,
        x="month",
        y="total_spent",
        markers=True,
        labels={"total_spent": "Total Spent ($)", "month": "Month"},
        text=monthly_df["total_spent"].apply(lambda x: f"${x:,.0f}"),
    )
    fig.update_traces(textposition="top center")
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, width='stretch')

    st.subheader("Monthly Breakdown by Category")

    monthly_cat_df = load_monthly_by_category()
    monthly_cat_df["month"] = pd.to_datetime(monthly_cat_df["month"]).dt.strftime("%Y-%m")

    fig2 = px.bar(
        monthly_cat_df,
        x="month",
        y="total_spent",
        color="category",
        labels={"total_spent": "Total Spent ($)", "month": "Month", "category": "Category"},
        barmode="stack",
    )
    fig2.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig2, width='stretch')

with tab3:
    st.subheader("Top 20 Merchants by Total Spending")

    merchants_df = load_top_merchants()

    fig = px.bar(
        merchants_df,
        x="total_spent",
        y="merchant_name",
        orientation="h",
        color="category",
        text=merchants_df["total_spent"].apply(lambda x: f"${x:,.0f}"),
        labels={"total_spent": "Total Spent ($)", "merchant_name": "Merchant"},
        hover_data=["visit_count", "avg_transaction"],
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=600)
    st.plotly_chart(fig, width='stretch')

with tab4:
    st.subheader("Spending by Card")

    cards_df = load_card_stats()

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            cards_df,
            x="card_name",
            y="total_spent",
            color="card_name",
            text=cards_df["total_spent"].apply(lambda x: f"${x:,.0f}"),
            labels={"total_spent": "Total Spent ($)", "card_name": "Card"},
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, width='stretch')

    with col2:
        display_df = cards_df[["card_name", "total_spent", "transaction_count", "unique_merchants", "avg_transaction"]].copy()
        display_df.columns = ["Card", "Total ($)", "Transactions", "Merchants", "Avg ($)"]
        display_df["Total ($)"] = display_df["Total ($)"].apply(lambda x: f"${x:,.2f}")
        display_df["Avg ($)"] = display_df["Avg ($)"].apply(lambda x: f"${x:,.2f}")
        st.dataframe(display_df, hide_index=True, width='stretch')
