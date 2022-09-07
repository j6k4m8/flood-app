from flask import Flask, render_template, request
import matplotlib.pyplot as plt

app = Flask(__name__)


import pandas as pd
import re
import matplotlib.pyplot as plt

def get_hydrograph_observed_and_forecast(
    sensor_id: str = "phdp1", units_in_columns: bool = False
):
    url = f"https://water.weather.gov/ahps2/hydrograph_to_xml.php?gage={sensor_id}&output=tabular&time_zone=edt"
    cur_year = pd.Timestamp.now().year
    dfs = pd.read_html(url)
    historical = dfs[1][2:]
    historical.columns = ["Date", "Stage", "Flow"]
    # Format of date is "MM/DD HH:MM", so we need to add the year
    historical.loc[:, "Date"] = historical["Date"].apply(lambda x: f"{cur_year} {x}")
    historical.loc[:, "Date"] = pd.to_datetime(
        historical["Date"], format="%Y %m/%d %H:%M"
    )

    historical.loc[:, "Stage"] = (
        historical["Stage"].apply(lambda x: x.replace("ft", "")).astype(float)
    )
    historical.loc[:, "Flow"] = (
        historical["Flow"].apply(lambda x: x.replace("kcfs", "")).astype(float)
    )
    historical = historical.set_index("Date")
    if units_in_columns:
        historical = historical.rename(
            columns={
                "Flow": "Flow(kcfs)",
                "Stage": "Stage(ft)",
                "Date": "Date(EDT)",
            }
        )

    forecast = dfs[2][2:]
    forecast.columns = ["Date", "Stage", "Flow"]
    forecast.loc[:, "Date"] = forecast["Date"].apply(lambda x: f"{cur_year} {x}")
    forecast.loc[:, "Date"] = pd.to_datetime(forecast["Date"], format="%Y %m/%d %H:%M")

    forecast.loc[:, "Stage"] = (
        forecast["Stage"].apply(lambda x: x.replace("ft", "")).astype(float)
    )
    forecast.loc[:, "Flow"] = (
        forecast["Flow"].apply(lambda x: x.replace("kcfs", "")).astype(float)
    )
    forecast = forecast.set_index("Date")

    if units_in_columns:
        forecast = forecast.rename(
            columns={
                "Flow": "Flow(kcfs)",
                "Stage": "Stage(ft)",
                "Date": "Date(EDT)",
            }
        )

    return historical, forecast


def get_metadata_for_hydrograph(sensor_id: str = "phdp1"):
    url = f"https://water.weather.gov/ahps2/metadata.php?wfo=phi&gage={sensor_id}"
    dfs = pd.read_html(url)
    latlng = dfs[1] # Of the format "Latitude: 40.0000° N, Longitude: -75.0000° W"
    latlng_str = latlng.iloc[0][0]
    lat = float(re.search(r'Latitude: (.*)° N', latlng_str).group(1))
    lng = float(re.search(r'Longitude: (.*)° W', latlng_str).group(1))
    metadata = dfs[2]
    flood_stage = float(metadata['Flood Stage'].iloc[0].replace("ft", ""))
    return {
        'lat': lat,
        'lng': lng,
        'flood_stage': flood_stage
    }



@app.route('/plot')
def plot():

    sensor_id = request.args.get("site", "phdp1")
    metadata = get_metadata_for_hydrograph(sensor_id)
    historical, forecast = get_hydrograph_observed_and_forecast(sensor_id)
    with plt.style.context("bmh"):
        plt.figure(figsize=(6, 3), dpi=100)
        print(len(historical.Stage))
        historical.Stage.plot(
            ylabel="Stage (ft)", title=f"{sensor_id} Hydrograph Stage"
        )
        forecast.Stage.plot(ylabel="Stage (ft)")
        plt.axhline(metadata["flood_stage"], color="red", linestyle="--")
    plt.savefig('static/images/plot.svg')

    return render_template('plot.html', url='/static/images/plot.svg')

if __name__ == '__main__':
   app.run(host="0.0.0.0", port=8022)
