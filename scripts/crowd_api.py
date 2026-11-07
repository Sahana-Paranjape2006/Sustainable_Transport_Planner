from flask import Flask, request, jsonify

from scripts.assess_route_crowd import assess_route_crowd

app = Flask(__name__)


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Metro Crowd Assessment API is running",
        "status": "OK"
    })


@app.route("/api/crowd/assess", methods=["POST"])
def assess_crowd():
    try:
        data = request.get_json(silent=True) or {}

        route_stations = data.get("route_stations")
        date = data.get("date")
        hour = data.get("hour")

        if not isinstance(route_stations, list) or not route_stations:
            return jsonify({
                "error": "A non-empty route_stations list is required."
            }), 400

        if not all(
            isinstance(station, str) and station.strip()
            for station in route_stations
        ):
            return jsonify({
                "error": "Every station must be a non-empty string."
            }), 400

        if not date:
            return jsonify({
                "error": "Date is required."
            }), 400

        if (
            isinstance(hour, bool)
            or not isinstance(hour, int)
            or not 0 <= hour <= 23
        ):
            return jsonify({
                "error": "Hour must be an integer between 0 and 23."
            }), 400

        result = assess_route_crowd(
            route_stations=route_stations,
            date=date,
            hour=hour
        )

        return jsonify(result), 200

    except Exception as error:
        return jsonify({
            "error": str(error)
        }), 500


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5002,
        debug=False
    )