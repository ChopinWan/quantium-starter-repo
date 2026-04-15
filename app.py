from pathlib import Path

import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html


DATA_PATH = Path(__file__).parent / "data" / "daily_sales_data_2.csv"
PRICE_INCREASE_DATE = pd.Timestamp("2021-01-15")


def load_daily_sales() -> pd.DataFrame:
    """Load daily sales and aggregate to a single total-sales series by date."""
    daily_sales = pd.read_csv(DATA_PATH)
    daily_sales["Date"] = pd.to_datetime(daily_sales["Date"])

    # Keep this robust in case the source data has per-region rows or already-total rows.
    grouped_sales = (
        daily_sales.groupby("Date", as_index=False)["Sales"].sum().sort_values("Date")
    )

    grouped_sales["Period"] = grouped_sales["Date"].apply(
        lambda date: "Before 2021-01-15" if date < PRICE_INCREASE_DATE else "After 2021-01-15"
    )
    return grouped_sales


def build_figure(data: pd.DataFrame):
    before_avg = data.loc[data["Date"] < PRICE_INCREASE_DATE, "Sales"].mean()
    after_avg = data.loc[data["Date"] >= PRICE_INCREASE_DATE, "Sales"].mean()

    figure = px.line(
        data,
        x="Date",
        y="Sales",
        title=(
            "Total Daily Pink Morsel Sales\n"
            f"Average before: ${before_avg:,.2f} | Average after: ${after_avg:,.2f}"
        ),
        labels={"Date": "Date", "Sales": "Total Sales (USD)"},
    )

    figure.add_vline(
        x=PRICE_INCREASE_DATE,
        line_dash="dash",
        line_width=2,
        line_color="#B54708",
        annotation_text="Price increase (2021-01-15)",
        annotation_position="top left",
    )

    figure.update_layout(
        title_x=0.5,
        template="plotly_white",
        margin={"l": 40, "r": 20, "t": 80, "b": 40},
    )
    return figure


def create_app() -> Dash:
    sales_data = load_daily_sales()
    figure = build_figure(sales_data)

    app = Dash(__name__)
    app.title = "Soul Foods Sales Visualiser"

    app.layout = html.Div(
        [
            html.H1("Soul Foods: Pink Morsel Sales Before vs After Price Increase"),
            dcc.Graph(figure=figure),
        ],
        style={"maxWidth": "1100px", "margin": "0 auto", "padding": "24px"},
    )

    return app


app = create_app()
server = app.server


if __name__ == "__main__":
    app.run(debug=True)
