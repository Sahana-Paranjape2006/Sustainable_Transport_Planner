
const express = require("express");
const cors = require("cors");

const {
  findMetroRoute,
  loadMetroNetwork
} = require("./metro_route_engine");

const app = express();
const PORT = 5001;

const CROWD_API_URL =
  "http://127.0.0.1:5002/api/crowd/assess";

app.use(cors());
app.use(express.json());


// --------------------------------------------------
// 1. Check whether the Metro API is running
// --------------------------------------------------

app.get("/", (req, res) => {
  res.json({
    message: "Metro Route API is running",
    status: "OK"
  });
});


// --------------------------------------------------
// 2. Get Metro stations for frontend dropdowns
// --------------------------------------------------

app.get("/api/metro/stations", (req, res) => {
  try {
    const rows = loadMetroNetwork();

    const stations = rows
      .filter(row =>
        row.station_code &&
        row.station_name &&
        row.line
      )
      .map(row => ({
        station_code: row.station_code,
        station_name: row.station_name,
        line: row.line
      }));

    // Remove duplicate station-code and line combinations
    const uniqueStations = Array.from(
      new Map(
        stations.map(station => [
          `${station.station_code}__${station.line}`,
          station
        ])
      ).values()
    );

    uniqueStations.sort((a, b) =>
      a.station_name.localeCompare(b.station_name) ||
      a.line.localeCompare(b.line)
    );

    res.json({
      total_stations: uniqueStations.length,
      stations: uniqueStations
    });

  } catch (error) {
    console.error("Metro station loading error:", error);

    res.status(500).json({
      error: error.message
    });
  }
});


// --------------------------------------------------
// 3. Generate Metro route and assess crowd level
// --------------------------------------------------

app.get("/api/metro/route", async (req, res) => {
  try {
    const {
      start,
      destination,
      startLine,
      destinationLine,
      date,
      hour
    } = req.query;


    // Validate required station information

    if (!start || !destination) {
      return res.status(400).json({
        error:
          "Both starting and destination station codes are required."
      });
    }


    // Validate date and hour

    if (!date || hour === undefined) {
      return res.status(400).json({
        error:
          "Date and hour are required for crowd assessment."
      });
    }

    const parsedHour = Number(hour);

    if (
      !Number.isInteger(parsedHour) ||
      parsedHour < 0 ||
      parsedHour > 23
    ) {
      return res.status(400).json({
        error: "Hour must be an integer between 0 and 23."
      });
    }


    // Step 1: Generate Metro route using Dijkstra

    const metroResult = findMetroRoute(
      start,
      destination,
      startLine || null,
      destinationLine || null
    );

    if (!metroResult.found) {
      return res.status(404).json(metroResult);
    }


    // Step 2: Extract station names in route order

    const routeStations = metroResult.route.map(
      station => station.station_name
    );


    // Step 3: Send route to Python Crowd Assessment API

    const crowdResponse = await fetch(CROWD_API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        route_stations: routeStations,
        date: date,
        hour: parsedHour
      })
    });

    const crowdResult = await crowdResponse.json();

    if (!crowdResponse.ok) {
      return res.status(502).json({
        error: "Crowd assessment failed.",
        details: crowdResult
      });
    }


    // Step 4: Return combined route and crowd results

    res.json({
      found: true,
      metro_route: metroResult,
      crowd_assessment: crowdResult
    });

  } catch (error) {
    console.error("Metro route integration error:", error);

    res.status(500).json({
      error: error.message
    });
  }
});


// --------------------------------------------------
// 4. Start Metro API server
// --------------------------------------------------

app.listen(PORT, () => {
  console.log(
    `Metro Route API running at http://localhost:${PORT}`
  );
});
