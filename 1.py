import numpy as np

import pandas as pd

import plotly.express as px

from dash import Dash, Input, Output, dcc, html

# ============================================================
# 1. DATA LAYER
# ============================================================

rng = np.random.default_rng(42)
n = 5000

df = pd.DataFrame({
    "date": (
        pd.to_datetime("2025-01-01")
        + pd.to_timedelta(
            rng.integers(0, 365, n),
            unit="D"
        )
    ),

    "region": rng.choice(
        ["North", "South", "East", "West"], n
    ),

    "category": rng.choice(
        ["Electronics", "Clothing", "Home", "Sports"], n
    ),

    "units": rng.integers(1, 10, n),
    "unit_price": rng.uniform(10, 200, n).round(2),
})

df["revenue"] = df["units"] * df["unit_price"]

# ============================================================
# 2. APP AND LAYOUT
# ============================================================

app = Dash(__name__)
app.title = "Sales Dashboard"

CARD = {
    "background": "#f7f7f9",
    "padding": "16px",
    "borderRadius": "8px",
    "textAlign": "center",
    "flex": "1",
    "boxShadow": "0 2px 6px rgba(0,0,0,0.08)",
}

regions_list = sorted(df["region"].unique())
categories_list = sorted(df["category"].unique())

app.layout = html.Div(
    style={
        "fontFamily": "Arial, sans-serif",
        "padding": "20px",
        "maxWidth": "1200px",
        "margin": "auto",
    },
    children=[
        html.H1("Sales Performance Dashboard"),

        html.P(
            "Interactive sales analysis by region, category and date."
        ),

        # Filters
        html.Div(
            style={
                "display": "flex",
                "gap": "20px",
                "marginBottom": "20px",
                "flexWrap": "wrap",
            },

            children=[
                html.Div(
                    style={"flex": "1", "minWidth": "180px"},
                    children=[
                        html.Label("Region"),
                        dcc.Dropdown(
                            id="region-filter",
                            options=[
                                {"label": r, "value": r}
                                for r in regions_list
                            ],

                            value=regions_list,
                            multi=True,
                            placeholder="Select region",
                        ),
                    ],
                ),

                html.Div(
                    style={"flex": "1", "minWidth": "180px"},
                    children=[
                        html.Label("Category"),
                        dcc.Dropdown(
                            id="category-filter",
                            options=[
                                {"label": c, "value": c}
                                for c in categories_list
                            ],
                            value=categories_list,
                            multi=True,
                            placeholder="Select category",
                        ),
                    ],
                ),

                html.Div(
                    style={"flex": "1", "minWidth": "260px"},
                    children=[
                        html.Label("Date Range"),
                        dcc.DatePickerRange(
                            id="date-filter",
                            min_date_allowed=df["date"].min().date(),
                            max_date_allowed=df["date"].max().date(),
                            start_date=df["date"].min().date(),
                            end_date=df["date"].max().date(),
                            display_format="DD-MM-YYYY",
                        ),
                    ],
                ),
            ],
        ),

        # KPI Cards
        html.Div(
            id="kpi-row",
            style={
                "display": "flex",
                "gap": "16px",
                "marginBottom": "20px",
                "flexWrap": "wrap",
            },
        ),

        # Monthly trend chart
        dcc.Graph(id="trend-chart"),

        # Category and region charts
        html.Div(
            style={
                "display": "flex",
                "gap": "20px",
                "flexWrap": "wrap",
            },
            children=[
                html.Div(
                    dcc.Graph(id="category-chart"),
                    style={"flex": "1", "minWidth": "300px"},
                ),
                html.Div(
                    dcc.Graph(id="region-chart"),
                    style={"flex": "1", "minWidth": "300px"},
                ),
            ],
        ),
    ],
)

# ============================================================
# 3. HELPER FUNCTIONS
# ============================================================

def filter_data(regions, categories, start, end):

    if not start or not end:
        return df.iloc[0:0].copy()

    if not regions or not categories:
        return df.iloc[0:0].copy()

    start_date = pd.to_datetime(start)

    end_date = (
        pd.to_datetime(end) + pd.Timedelta(days=1)
        - pd.Timedelta(microseconds=1)
    )

    filtered = df[
        df["region"].isin(regions)
        & df["category"].isin(categories)
        & df["date"].between(start_date, end_date)
    ]

    return filtered.copy()


def kpi_card(title, value):

    return html.Div(
        style=CARD,
        children=[
            html.Div(
                title,
                style={"color": "#666", "fontSize": "14px"},
            ),
            html.H2(
                value,
                style={"margin": "4px 0 0", "color": "#222"},
            ),
        ],
    )

# ============================================================
# 4. CALLBACKS
# ============================================================

@app.callback(
    Output("kpi-row", "children"),
    Output("trend-chart", "figure"),
    Output("category-chart", "figure"),
    Output("region-chart", "figure"),
    Input("region-filter", "value"),
    Input("category-filter", "value"),
    Input("date-filter", "start_date"),
    Input("date-filter", "end_date"),
)

def update_dashboard(regions, categories, start, end):

    d = filter_data(regions, categories, start, end)

    # Handle empty data
    if d.empty:

        empty_fig = px.scatter(
            title="No data for the selected filters"
        )

        empty_kpis = [
            kpi_card("Total Revenue", "$0.00"),
            kpi_card("Orders", "0"),
            kpi_card("Avg Order Value", "$0.00"),
            kpi_card("Units Sold", "0"),
        ]

        return empty_kpis, empty_fig, empty_fig, empty_fig

    # KPI Cards
    total_revenue = d["revenue"].sum()
    total_orders = len(d)
    avg_order_value = d["revenue"].mean()
    total_units = d["units"].sum()

    kpis = [
        kpi_card("Total Revenue", f"${total_revenue:,.2f}"),
        kpi_card("Orders", f"{total_orders:,}"),
        kpi_card("Avg Order Value", f"${avg_order_value:,.2f}"),
        kpi_card("Units Sold", f"{total_units:,}"),
    ]

    # Monthly Revenue Trend
    monthly = (
        d.set_index("date")
        .resample("MS")["revenue"]
        .sum()
        .reset_index()
    )

    fig_trend = px.line(
        monthly,
        x="date",
        y="revenue",
        markers=True,
        title="Monthly Revenue Trend",
        labels={
            "date": "Month",
            "revenue": "Revenue ($)",
        },
    )

    fig_trend.update_layout(
        template="plotly_white",
        hovermode="x unified",
    )

    # Revenue by Category
    by_cat = (
        d.groupby("category", as_index=False)["revenue"]
        .sum()
        .sort_values("revenue", ascending=True)
    )

    fig_cat = px.bar(
        by_cat,
        x="revenue",
        y="category",
        orientation="h",
        title="Revenue by Category",
        labels={
            "revenue": "Revenue ($)",
            "category": "Category",
        },
    )

    fig_cat.update_layout(template="plotly_white")

    # Revenue by Region
    by_reg = (
        d.groupby("region", as_index=False)["revenue"]
        .sum()
        .sort_values("revenue", ascending=False)
    )

    fig_reg = px.bar(
        by_reg,
        x="region",
        y="revenue",
        title="Revenue by Region",
        labels={
            "region": "Region",
            "revenue": "Revenue ($)",
        },
    )

    fig_reg.update_layout(template="plotly_white")

    return kpis, fig_trend, fig_cat, fig_reg

# ============================================================
# 5. RUN APPLICATION
# ============================================================

if __name__ == "__main__":
    app.run(debug=True)