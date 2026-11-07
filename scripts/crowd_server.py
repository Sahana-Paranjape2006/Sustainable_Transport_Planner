
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
        data = request.get_json()

        if not data:
            return jsonify({
                "error": "Request body must contain JSON data."
            }), 400

        route_stations = data.get("route_stations")
        date = data.get("date")
        hour = data.get("hour")

        if not route_stations or not date or hour is None:
            return jsonify({
                "error": "route_stations, date and hour are required."
            }), 400

        if not isinstance(route_stations, list):
            return jsonify({
                "error": "route_stations must be a list."
            }), 400

        if isinstance(hour, bool) or not isinstance(hour, int):
            return jsonify({
                "error": "hour must be an integer."
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
