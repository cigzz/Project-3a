from flask import Flask, render_template, request
import csv
import requests
import pygal
from datetime import datetime

app = Flask(__name__)

API_KEY = "W13CLXEETOOJXKNL"
CSV_FILE = "stocks.csv"


# load stock symbols
def load_symbols():
    symbols = []
    with open(CSV_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            symbols.append(row["Symbol"])
    return symbols


# fetch data
def fetch_time_series(symbol, ts_type):
    function_map = {
        "daily": "TIME_SERIES_DAILY",
        "weekly": "TIME_SERIES_WEEKLY",
        "monthly": "TIME_SERIES_MONTHLY"
    }

    url = (
        f"https://www.alphavantage.co/query?"
        f"function={function_map[ts_type]}&symbol={symbol}&apikey={API_KEY}"
    )

    response = requests.get(url)
    data = response.json()

    # extract correct time series key
    ts_keys = {
        "daily": "Time Series (Daily)",
        "weekly": "Weekly Time Series",
        "monthly": "Monthly Time Series"
    }

    if ts_keys[ts_type] not in data:
        return None

    return data[ts_keys[ts_type]]


# create chart
def generate_chart(chart_type, symbol, ts, start, end):
    # filter date range
    dates = sorted([d for d in ts.keys() if start <= d <= end])

    highs = [float(ts[d]["2. high"]) for d in dates]

    # pygal chart setup
    if chart_type == "line":
        chart = pygal.Line()
    else:
        chart = pygal.Bar()

    chart.title = f"{symbol.upper()} High Price ({start} → {end})"
    chart.x_labels = dates
    chart.add("High", highs)

    chart_path = "static/chart.svg"
    chart.render_to_file(chart_path)
    return chart_path


# Routes
@app.route("/", methods=["GET", "POST"])
def index():
    symbols = load_symbols()
    error = None
    chart_path = None

    if request.method == "POST":
        # get inputs
        symbol = request.form.get("symbol")
        chart_type = request.form.get("chart_type")
        ts_type = request.form.get("time_series")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")

        # validation

        # symbol
        if symbol not in symbols:
            error = "Invalid stock symbol."
            return render_template("index.html", symbols=symbols, error=error)

        # chart type
        if chart_type not in ["line", "bar"]:
            error = "Invalid chart type. Choose line or bar."
            return render_template("index.html", symbols=symbols, error=error)

        # time series
        if ts_type not in ["daily", "weekly", "monthly"]:
            error = "Invalid time series option."
            return render_template("index.html", symbols=symbols, error=error)

        # date validation
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
        except:
            error = "Invalid start date."
            return render_template("index.html", symbols=symbols, error=error)

        try:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except:
            error = "Invalid end date."
            return render_template("index.html", symbols=symbols, error=error)

        if end < start:
            error = "End date must be after start date."
            return render_template("index.html", symbols=symbols, error=error)

        # API Call
        ts = fetch_time_series(symbol, ts_type)
        if ts is None:
            error = "API returned no data. Try another symbol or time series."
            return render_template("index.html", symbols=symbols, error=error)

        # chart generation
        chart_path = generate_chart(chart_type, symbol, ts, str(start), str(end))

    return render_template("index.html",
                           symbols=symbols,
                           error=error,
                           chart_path=chart_path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)