from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, dcc, html


DATA_PATH = Path(__file__).parent / "data" / "daily_sales_data_2.csv"
PRICE_INCREASE_DATE = pd.Timestamp("2021-01-15")
REGIONS = ["north", "east", "south", "west"]
RADIO_OPTIONS = [{"label": "all", "value": "all"}] + [
    {"label": region, "value": region} for region in REGIONS
]


def load_daily_sales() -> pd.DataFrame:
    """Load and return Pink Morsel daily sales by date and region."""
    daily_sales = pd.read_csv(DATA_PATH)

    if {"Date", "Sales", "Region"}.issubset(daily_sales.columns):
        # Support pre-aggregated data from the previous task.
        working = daily_sales[["Date", "Sales", "Region"]].copy()
        working["Date"] = pd.to_datetime(working["Date"], format="mixed", errors="coerce")
        working["Region"] = working["Region"].astype(str).str.strip().str.lower()

        grouped_sales = (
            working.dropna(subset=["Date"])
            .groupby(["Date", "Region"], as_index=False)["Sales"]
            .sum()
            .sort_values("Date")
        )
    else:
        # Support raw row-level data by deriving Pink Morsel revenue: price * quantity.
        raw = daily_sales.copy()
        raw.columns = [col.strip().lower() for col in raw.columns]

        pink_sales = raw.loc[raw["product"].str.lower() == "pink morsel"].copy()
        pink_sales["date"] = pd.to_datetime(pink_sales["date"], format="mixed", errors="coerce")
        pink_sales["region"] = pink_sales["region"].astype(str).str.strip().str.lower()
        pink_sales["price"] = (
            pink_sales["price"].astype(str).str.replace("$", "", regex=False).astype(float)
        )
        pink_sales["quantity"] = pd.to_numeric(pink_sales["quantity"], errors="coerce")
        pink_sales["sales"] = pink_sales["price"] * pink_sales["quantity"]

        grouped_sales = (
            pink_sales.dropna(subset=["date", "quantity"]) 
            .groupby(["date", "region"], as_index=False)["sales"]
            .sum()
            .rename(columns={"date": "Date", "region": "Region", "sales": "Sales"})
            .sort_values("Date")
        )

    return grouped_sales


def build_figure(data: pd.DataFrame, selected_region: str) -> go.Figure:
    if selected_region == "all":
        filtered = data.groupby("Date", as_index=False)["Sales"].sum().sort_values("Date")
        region_label = "All Regions"
    else:
        filtered = (
            data.loc[data["Region"] == selected_region]
            .groupby("Date", as_index=False)["Sales"]
            .sum()
            .sort_values("Date")
        )
        region_label = selected_region.title()

    if filtered.empty:
        empty_figure = go.Figure()
        empty_figure.update_layout(
            title=f"No Pink Morsel data available for {region_label}",
            xaxis_title="Date",
            yaxis_title="Total Sales (USD)",
            template="plotly_white",
        )
        return empty_figure

    before_avg = filtered.loc[filtered["Date"] < PRICE_INCREASE_DATE, "Sales"].mean()
    after_avg = filtered.loc[filtered["Date"] >= PRICE_INCREASE_DATE, "Sales"].mean()

    figure = px.line(
        filtered,
        x="Date",
        y="Sales",
        title=(
            f"Total Daily Pink Morsel Sales - {region_label}\n"
            f"Average before: ${before_avg:,.2f} | Average after: ${after_avg:,.2f}"
        ),
        labels={"Date": "Date", "Sales": "Total Sales (USD)"},
    )

    marker_x = PRICE_INCREASE_DATE.strftime("%Y-%m-%d")
    figure.add_shape(
        type="line",
        x0=marker_x,
        x1=marker_x,
        y0=0,
        y1=1,
        xref="x",
        yref="paper",
        line={"dash": "dash", "width": 2, "color": "#B54708"},
    )
    figure.add_annotation(
        x=marker_x,
        y=1,
        xref="x",
        yref="paper",
        text="Price increase (2021-01-15)",
        showarrow=False,
        xanchor="left",
        yanchor="bottom",
    )

    figure.update_layout(
        title_x=0.5,
        template="plotly_white",
        margin={"l": 40, "r": 20, "t": 80, "b": 40},
        plot_bgcolor="#F7EFE3",
        paper_bgcolor="#F7EFE3",
    )
    figure.update_traces(line={"color": "#C44536", "width": 3})
    return figure


def create_app() -> Dash:
    sales_data = load_daily_sales()
    figure = build_figure(sales_data, "all")

    app = Dash(__name__)
    app.title = "Soul Foods Sales Visualiser"

    app.layout = html.Div(
        children=[
            html.Div(
                className="hero-card",
                children=[
                    html.H1("Soul Foods Pink Morsel Sales Explorer", className="title"),
                    html.P(
                        "Use the region filter to compare Pink Morsel sales before and after the 15 Jan 2021 price increase.",
                        className="subtitle",
                    ),
                ],
            ),
            html.Div(
                className="control-card",
                children=[
                    html.Label("Choose Region", htmlFor="region-filter", className="control-label"),
                    dcc.RadioItems(
                        id="region-filter",
                        options=RADIO_OPTIONS,
                        value="all",
                        inline=True,
                        className="region-radio-group",
                        labelClassName="region-radio-label",
                    ),
                ],
            ),
            html.Div(
                className="chart-card",
                children=[
                    dcc.Graph(id="sales-line-chart", figure=figure),
                ],
            ),
        ],
        className="app-shell",
    )

    @app.callback(Output("sales-line-chart", "figure"), Input("region-filter", "value"))
    def update_chart(selected_region: str) -> go.Figure:
        return build_figure(sales_data, selected_region)

    return app


app = create_app()
server = app.server


if __name__ == "__main__":
    app.run(debug=True)
