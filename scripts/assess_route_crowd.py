
from pathlib import Path

import pandas as pd
from scripts.predict_crowd import predict_crowd


# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
MAPPING_PATH = (
    PROJECT_ROOT
    / "data"
    / "Processed"
    / "crowd"
    / "station_mapping1.csv"
)

CROWD_RANK = {
    "Low": 1,
    "Medium": 2,
    "High": 3,
}

CROWD_LEVELS = ["Low", "Medium", "High"]


def load_station_mapping():
    if not MAPPING_PATH.exists():
        raise FileNotFoundError(
            f"Station mapping file not found: {MAPPING_PATH}"
        )

    df = pd.read_csv(MAPPING_PATH)

    required_columns = {
        "metro_station_name",
        "crowd_station_name",
    }

    if not required_columns.issubset(df.columns):
        raise ValueError(
            "station_mapping1.csv must contain "
            "'metro_station_name' and 'crowd_station_name'."
        )

    return dict(
        zip(
            df["metro_station_name"].str.strip(),
            df["crowd_station_name"].str.strip(),
        )
    )


def assess_route_crowd(route_stations, date, hour):

    if not route_stations:
        raise ValueError("The route must contain at least one station.")

    if not isinstance(hour, int) or not 0 <= hour <= 23:
        raise ValueError("Hour must be an integer between 0 and 23.")

    station_mapping = load_station_mapping()
    station_results = []

    # Predict crowd level at every station
    for metro_station in route_stations:
        metro_station = metro_station.strip()

        crowd_station = station_mapping.get(
            metro_station,
            metro_station,
        )

        prediction = predict_crowd(
            station=crowd_station,
            date=date,
            hour=hour,
        )

        station_results.append({
            "metro_station": metro_station,
            "crowd_station": crowd_station,
            "predicted_crowd_level": (
                prediction["predicted_crowd_level"]
            ),
        })

    # Count stations in each crowd category
    total_stations = len(station_results)

    crowd_counts = {
        level: sum(
            1
            for station in station_results
            if station["predicted_crowd_level"] == level
        )
        for level in CROWD_LEVELS
    }

    # Calculate crowd percentages
    crowd_percentages = {
        level: round(
            (crowd_counts[level] / total_stations) * 100, 2
        )
        for level in CROWD_LEVELS
    }

    # Find the highest crowd level on the route
    overall_level = max(
        (
            result["predicted_crowd_level"]
            for result in station_results
        ),
        key=lambda level: CROWD_RANK[level],
    )

    # Identify bottleneck stations
    highest_rank = CROWD_RANK[overall_level]

    bottleneck_stations = [
        station["metro_station"]
        for station in station_results
        if CROWD_RANK[station["predicted_crowd_level"]]
        == highest_rank
    ]

    # Calculate average route crowd score
    average_weight = sum(
        CROWD_RANK[station["predicted_crowd_level"]]
        for station in station_results
    ) / total_stations

    route_crowd_score = round(
        ((average_weight - 1) / 2) * 100,
        2,
    )

    # Determine average route crowd category
    if route_crowd_score < 33.33:
        route_average_crowd_level = "Low"
    elif route_crowd_score < 66.67:
        route_average_crowd_level = "Medium"
    else:
        route_average_crowd_level = "High"

    return {
        "date": date,
        "hour": hour,
        "total_stations": total_stations,
        "station_predictions": station_results,
        "overall_route_crowd_indicator": overall_level,
        "crowd_counts": crowd_counts,
        "crowd_percentages": crowd_percentages,
        "bottleneck_stations": bottleneck_stations,
        "route_crowd_score": route_crowd_score,
        "route_average_crowd_level": route_average_crowd_level,
    }


if __name__ == "__main__":

    ROUTE_STATIONS = [
        "Nadaprabhu Kempegowda Station Majestic",
        "Chickpete",
        "Krishna Rajendra Market",
        "National College",
        "Lalbagh",
        "South End Circle",
        "Jayanagar",
        "Rashtreeya Vidyalaya Road",
    ]

    result = assess_route_crowd(
        route_stations=ROUTE_STATIONS,
        date="2025-09-30",
        hour=18,
    )

    print("\n===== ROUTE CROWD ASSESSMENT =====")
    print("Date:", result["date"])
    print("Hour:", result["hour"])
    print("Total stations:", result["total_stations"])

    print(
        "Overall route crowd indicator:",
        result["overall_route_crowd_indicator"],
    )

    print(
        "Route crowd score:",
        result["route_crowd_score"],
        "/ 100",
    )

    print(
        "Average route crowd level:",
        result["route_average_crowd_level"],
    )

    print("\n===== CROWD DISTRIBUTION =====")

    for level in CROWD_LEVELS:
        print(
            f"{level}: {result['crowd_counts'][level]} stations "
            f"({result['crowd_percentages'][level]}%)"
        )

    print("\n===== BOTTLENECK STATIONS =====")

    for station in result["bottleneck_stations"]:
        print(station)

    print("\n===== INDIVIDUAL STATION PREDICTIONS =====")

    for station in result["station_predictions"]:
        print(
            station["metro_station"],
            "->",
            station["predicted_crowd_level"],
        )
