const express = require("express");
const cors = require("cors");
const { findMetroRoute } = require("./metro_route_engine");

const app = express();
const PORT = 5001;

app.use(cors());
app.use(express.json());

// Check whether the API is running
app.get("/", (req, res) => {
  res.json({
    message: "Metro Route API is running",
    status: "OK"
  });
});

// Calculate a Metro route
app.get("/api/metro/route", (req, res) => {
  try {
    const {
      start,
      destination,
      startLine,
      destinationLine
    } = req.query;

    if (!start || !destination) {
      return res.status(400).json({
        error: "Both start and destination station codes are required."
      });
    }

    const result = findMetroRoute(
      start,
      destination,
      startLine || null,
      destinationLine || null
    );

    if (!result.found) {
      return res.status(404).json(result);
    }

    res.json(result);
  } catch (error) {
    res.status(400).json({
      error: error.message
    });
  }
});

app.listen(PORT, () => {
  console.log(`Metro Route API running at http://localhost:${PORT}`);
});