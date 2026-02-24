import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
from datetime import date
import calendar
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Budget Tracker",
    page_icon="💰",
    layout="wide"
)

def check_password():
    if st.session_state.get("authenticated"):
        return True
    st.title("💰 Budget Tracker")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if password == os.getenv("DASHBOARD_PASSWORD", ""):
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password")
    return False

if not check_password():
    st.stop()

@st.cache_resource
def get_engine():
    connection_string = os.getenv(
        "SUPABASE_DB_URL",
        "postgresql://budget_user:budget_pass@localhost:5432/budget_tracker"
    )
    return create_engine(connection_string)

# Current month data functions
@st.cache_data(ttl=300)
def load_mtd_summary():
    engine = get_engine()
    return pd.read_sql("""
        SELECT
            SUM(CASE
                WHEN transaction_date >= DATE_TRUNC('month', CURRENT_DATE)
                AND transaction_date <= CURRENT_DATE
                THEN amount END) AS current_mtd,
            SUM(CASE
                WHEN transaction_date >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'
                AND EXTRACT(day FROM transaction_date) <= EXTRACT(day FROM CURRENT_DATE)
                AND transaction_date < DATE_TRUNC('month', CURRENT_DATE)
                THEN amount END) AS last_month_same_days,
            SUM(CASE
                WHEN transaction_date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 year')
                AND EXTRACT(day FROM transaction_date) <= EXTRACT(day FROM CURRENT_DATE)
                AND transaction_date < DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 year') + INTERVAL '1 month'
                THEN amount END) AS last_year_same_days
        FROM silver.transactions
    """, engine)

@st.cache_data(ttl=300)
def load_category_mtd():
    engine = get_engine()
    return pd.read_sql("""
        SELECT
            category,
            SUM(CASE
                WHEN transaction_date >= DATE_TRUNC('month', CURRENT_DATE)
                AND transaction_date <= CURRENT_DATE
                THEN amount ELSE 0 END) AS this_month,
            SUM(CASE
                WHEN transaction_date >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'
                AND EXTRACT(day FROM transaction_date) <= EXTRACT(day FROM CURRENT_DATE)
                AND transaction_date < DATE_TRUNC('month', CURRENT_DATE)
                THEN amount ELSE 0 END) AS last_month_same_days
        FROM silver.transactions
        WHERE
            (transaction_date >= DATE_TRUNC('month', CURRENT_DATE) AND transaction_date <= CURRENT_DATE)
            OR (
                transaction_date >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'
                AND EXTRACT(day FROM transaction_date) <= EXTRACT(day FROM CURRENT_DATE)
                AND transaction_date < DATE_TRUNC('month', CURRENT_DATE)
            )
        GROUP BY category
        ORDER BY this_month DESC
    """, engine)

@st.cache_data(ttl=300)
def load_daily_spending_curr():
    engine = get_engine()
    return pd.read_sql("""
        SELECT
            EXTRACT(day FROM transaction_date)::int AS day_num,
            SUM(amount) AS daily_amount
        FROM silver.transactions
        WHERE transaction_date >= DATE_TRUNC('month', CURRENT_DATE)
        AND transaction_date <= CURRENT_DATE
        GROUP BY day_num
        ORDER BY day_num
    """, engine)

@st.cache_data(ttl=300)
def load_daily_spending_prev():
    engine = get_engine()
    return pd.read_sql("""
        SELECT
            EXTRACT(day FROM transaction_date)::int AS day_num,
            SUM(amount) AS daily_amount
        FROM silver.transactions
        WHERE transaction_date >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'
        AND transaction_date < DATE_TRUNC('month', CURRENT_DATE)
        AND EXTRACT(day FROM transaction_date) <= EXTRACT(day FROM CURRENT_DATE)
        GROUP BY day_num
        ORDER BY day_num
    """, engine)

@st.cache_data(ttl=300)
def load_top_merchants_mtd():
    engine = get_engine()
    return pd.read_sql("""
        SELECT
            merchant_name,
            category,
            COUNT(*) AS visits,
            SUM(amount) AS total_spent
        FROM silver.transactions
        WHERE transaction_date >= DATE_TRUNC('month', CURRENT_DATE)
        AND transaction_date <= CURRENT_DATE
        GROUP BY merchant_name, category
        ORDER BY total_spent DESC
        LIMIT 10
    """, engine)

# Historical data functions
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

def pct_change(current, prior):
    if prior == 0 or prior is None:
        return None
    return ((current - prior) / prior) * 100

st.title("💰 Budget Tracker")
st.caption("Personal spending dashboard powered by Gmail transaction data")

tab_main, tab_history = st.tabs(["This Month", "Historical Deep Dive"])

with tab_main:
    today = date.today()
    day_of_month = today.day
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    month_name = today.strftime("%B %Y")
    last_month_dt = (today.replace(day=1) - pd.Timedelta(days=1))
    last_month_name = last_month_dt.strftime("%B")

    st.subheader(f"{month_name}  —  Day {day_of_month} of {days_in_month}")
    st.divider()

    summary = load_mtd_summary()
    current_mtd = float(summary["current_mtd"].iloc[0] or 0)
    last_month_sd = float(summary["last_month_same_days"].iloc[0] or 0)
    last_year_sd = float(summary["last_year_same_days"].iloc[0] or 0)
    daily_avg = current_mtd / day_of_month if day_of_month > 0 else 0
    projected = daily_avg * days_in_month

    mom_pct = pct_change(current_mtd, last_month_sd)
    yoy_pct = pct_change(current_mtd, last_year_sd)

    col1, col2, col3 = st.columns(3)
    with col1:
        delta_str = f"{mom_pct:+.1f}% vs {last_month_name} (same days)" if mom_pct is not None else None
        st.metric("Spent This Month (MTD)", f"${current_mtd:,.2f}", delta=delta_str, delta_color="inverse")
    with col2:
        st.metric("Projected Month-End", f"${projected:,.2f}", delta=f"${daily_avg:,.2f}/day avg", delta_color="off")
    with col3:
        yoy_str = f"{yoy_pct:+.1f}% vs last year (same days)" if yoy_pct is not None else None
        yoy_val = f"${last_year_sd:,.2f}" if last_year_sd > 0 else "No data"
        st.metric("vs. Last Year Same Period", yoy_val, delta=yoy_str, delta_color="inverse")

    st.divider()
    st.subheader(f"Spending by Category — {today.strftime('%b')} vs {last_month_name} (same {day_of_month} days)")

    cat_df = load_category_mtd()
    cat_df["change_pct"] = cat_df.apply(
        lambda r: pct_change(r["this_month"], r["last_month_same_days"]), axis=1
    )
    cat_df["change_str"] = cat_df["change_pct"].apply(
        lambda x: f"+{x:.1f}%" if x is not None and x >= 0 else (f"{x:.1f}%" if x is not None else "New")
    )

    cat_melted = cat_df.melt(
        id_vars="category",
        value_vars=["last_month_same_days", "this_month"],
        var_name="period",
        value_name="amount"
    )
    period_labels = {
        "last_month_same_days": f"{last_month_name} (same days)",
        "this_month": f"{today.strftime('%b')} MTD"
    }
    cat_melted["period"] = cat_melted["period"].map(period_labels)

    col1, col2 = st.columns([2, 1])
    with col1:
        fig = px.bar(
            cat_melted,
            x="amount",
            y="category",
            color="period",
            orientation="h",
            barmode="group",
            color_discrete_map={
                f"{last_month_name} (same days)": "#94a3b8",
                f"{today.strftime('%b')} MTD": "#3b82f6"
            },
            labels={"amount": "Amount ($)", "category": "Category", "period": "Period"},
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, legend_title="Period")
        st.plotly_chart(fig, width='stretch')

    with col2:
        display = cat_df[["category", "this_month", "last_month_same_days", "change_str"]].copy()
        display.columns = ["Category", f"{today.strftime('%b')} MTD", f"{last_month_name} Same Days", "MoM"]
        display[f"{today.strftime('%b')} MTD"] = display[f"{today.strftime('%b')} MTD"].apply(lambda x: f"${x:,.2f}")
        display[f"{last_month_name} Same Days"] = display[f"{last_month_name} Same Days"].apply(lambda x: f"${x:,.2f}")
        st.dataframe(display, hide_index=True, width='stretch')

    st.divider()
    st.subheader(f"Cumulative Spending — {today.strftime('%b')} vs {last_month_name}")

    curr_daily = load_daily_spending_curr().sort_values("day_num")
    prev_daily = load_daily_spending_prev().sort_values("day_num")
    curr_daily["cumulative"] = curr_daily["daily_amount"].cumsum()
    prev_daily["cumulative"] = prev_daily["daily_amount"].cumsum()

    fig_daily = go.Figure()
    fig_daily.add_trace(go.Scatter(
        x=curr_daily["day_num"],
        y=curr_daily["cumulative"],
        mode="lines+markers",
        name=f"{month_name}",
        line=dict(color="#3b82f6", width=2),
    ))
    fig_daily.add_trace(go.Scatter(
        x=prev_daily["day_num"],
        y=prev_daily["cumulative"],
        mode="lines",
        name=f"{last_month_name} (same days)",
        line=dict(color="#94a3b8", width=2, dash="dash"),
    ))
    fig_daily.update_layout(
        xaxis_title="Day of Month",
        yaxis_title="Cumulative Spent ($)",
        legend_title="Period",
    )
    st.plotly_chart(fig_daily, width='stretch')

    st.divider()
    st.subheader(f"Top Merchants — {today.strftime('%B')}")

    merch_df = load_top_merchants_mtd()
    col1, col2 = st.columns([2, 1])
    with col1:
        fig = px.bar(
            merch_df,
            x="total_spent",
            y="merchant_name",
            orientation="h",
            color="category",
            text=merch_df["total_spent"].apply(lambda x: f"${x:,.0f}"),
            labels={"total_spent": "Total Spent ($)", "merchant_name": "Merchant"},
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, width='stretch')

    with col2:
        display = merch_df[["merchant_name", "category", "visits", "total_spent"]].copy()
        display.columns = ["Merchant", "Category", "Visits", "Total ($)"]
        display["Total ($)"] = display["Total ($)"].apply(lambda x: f"${x:,.2f}")
        st.dataframe(display, hide_index=True, width='stretch')

with tab_history:
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

    hist1, hist2, hist3, hist4 = st.tabs(["Categories", "Monthly Trends", "Top Merchants", "Cards"])

    with hist1:
        available_years = load_available_years()
        selected_year = st.selectbox("Year", available_years, index=0)
        months_df = load_available_months(selected_year)
        month_options = months_df["month_name"].tolist()
        selected_month_names = st.multiselect("Month (optional)", month_options)
        month_map = dict(zip(months_df["month_name"], months_df["month_num"]))
        selected_month_nums = [month_map[m] for m in selected_month_names]
        label = f"{selected_year} - {', '.join(selected_month_names)}" if selected_month_names else str(selected_year)
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

    with hist2:
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

    with hist3:
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

    with hist4:
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
