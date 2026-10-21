
const express = require("express");
const cors = require("cors");
const dotenv = require("dotenv");
const fs = require("fs");
const path = require("path");
const csv = require("csv-parser");

dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;

const DATA_FILE = path.join(__dirname, "data", "routes.csv");
const STOPS_FILE = path.join(
  __dirname,
  "data",
  "BMTC_route_stops.csv"
);

app.use(cors());
app.use(express.json());

let routeData = [];
let allStops = [];
let stopIndex = new Map();
let sharedStops = new Set();
let stopCoordinates = new Map();
let dataLoaded = false;

// --------------------------------------------------
// BASIC CSV HELPERS
// --------------------------------------------------

function getField(row, names) {
  for (const name of names) {
    const key = Object.keys(row).find(
      (item) => item.trim().toLowerCase() === name.toLowerCase()
    );

    if (key && row[key] != null && String(row[key]).trim() !== "") {
      return String(row[key]).trim();
    }
  }

  return "";
}

function parseStopList(value) {
  if (!value) return [];

  const text = String(value).trim();

  try {
    const parsed = JSON.parse(text);

    if (Array.isArray(parsed)) {
      return parsed.map(String).map((s) => s.trim()).filter(Boolean);
    }
  } catch (_) {
    // Also support Python-style lists with single quotes.
  }

  const quotedStops = [...text.matchAll(/'([^']*)'|"([^"]*)"/g)]
    .map((match) => match[1] !== undefined ? match[1] : match[2])
    .map((stop) => stop.trim())
    .filter(Boolean);

  if (quotedStops.length) return quotedStops;

  return text
    .replace(/^\[|\]$/g, "")
    .split(/[;|]/)
    .map((stop) => stop.trim().replace(/^['"]|['"]$/g, ""))
    .filter(Boolean);
}

// --------------------------------------------------
// STOP NAME MATCHING
// --------------------------------------------------

function normalizeStop(value) {
  return String(value || "")
    .normalize("NFKD")
    .toLowerCase()
    .replace(/nildana|niladana|nilaya/g, "bus station")
    .replace(/bus\s+stand/g, "bus station")
    .replace(/[^a-z0-9\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function editDistance(a, b) {
  const previous = Array.from(
    { length: b.length + 1 },
    (_, index) => index
  );

  for (let i = 1; i <= a.length; i++) {
    let diagonal = previous[0];
    previous[0] = i;

    for (let j = 1; j <= b.length; j++) {
      const oldValue = previous[j];

      previous[j] = Math.min(
        previous[j] + 1,
        previous[j - 1] + 1,
        diagonal + (a[i - 1] === b[j - 1] ? 0 : 1)
      );

      diagonal = oldValue;
    }
  }

  return previous[b.length];
}

function similarity(a, b) {
  if (a === b) return 1;
  if (!a || !b) return 0;

  return 1 - editDistance(a, b) / Math.max(a.length, b.length);
}

function resolveStop(input) {
  const wanted = normalizeStop(input);

  if (!wanted) return null;

  const exact = allStops.find(
    (stop) => normalizeStop(stop) === wanted
  );

  if (exact) return exact;

  let bestStop = null;
  let bestScore = 0;

  for (const stop of allStops) {
    const score = similarity(wanted, normalizeStop(stop));

    if (score > bestScore) {
      bestScore = score;
      bestStop = stop;
    }
  }

  return bestScore >= 0.72 ? bestStop : null;
}

// --------------------------------------------------
// DISTANCE CALCULATION
// --------------------------------------------------

function haversineDistance(lat1, lon1, lat2, lon2) {
  const radians = (degrees) => degrees * Math.PI / 180;
  const earthRadiusKm = 6371;

  const dLat = radians(lat2 - lat1);
  const dLon = radians(lon2 - lon1);

  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(radians(lat1)) *
      Math.cos(radians(lat2)) *
      Math.sin(dLon / 2) ** 2;

  return 2 * earthRadiusKm *
    Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}



function getCoordinatesForStop(stopName) {
  const wanted = normalizeStop(stopName);

  if (!wanted) return null;

  // First: exact normalized stop-name match.
  const exact = stopCoordinates.get(wanted);

  if (exact) return exact;

  // Second: try a similar stop name.
  let bestCoordinates = null;
  let bestScore = 0;

  for (const [coordinateStopName, coordinates] of stopCoordinates.entries()) {
    const score = similarity(wanted, coordinateStopName);

    if (score > bestScore) {
      bestScore = score;
      bestCoordinates = coordinates;
    }
  }

  // Avoid matching completely different stops.
  return bestScore >= 0.75 ? bestCoordinates : null;
}

function calculateJourneyDistance(stops) {
  if (!Array.isArray(stops) || stops.length < 2) {
    return null;
  }

  const coordinates = stops.map(getCoordinatesForStop);

  const validCoordinate = (point) =>
    point &&
    Number.isFinite(point.lat) &&
    Number.isFinite(point.lon) &&
    (point.lat !== 0 || point.lon !== 0);

  // Use every stop when all stops have coordinates.
  if (coordinates.every(validCoordinate)) {
    let totalKm = 0;

    for (let i = 0; i < coordinates.length - 1; i++) {
      totalKm += haversineDistance(
        coordinates[i].lat,
        coordinates[i].lon,
        coordinates[i + 1].lat,
        coordinates[i + 1].lon
      );
    }

    return {
      distanceKm: Number(totalKm.toFixed(2)),
      distanceType: "stop_to_stop_estimate"
    };
  }

  // If some stops are missing coordinates, try the journey endpoints.
  const firstCoordinate = coordinates.find(validCoordinate);
  const lastCoordinate = [...coordinates].reverse().find(validCoordinate);

  if (!firstCoordinate || !lastCoordinate) {
    return null;
  }

  if (
    firstCoordinate.lat === lastCoordinate.lat &&
    firstCoordinate.lon === lastCoordinate.lon
  ) {
    return null;
  }

  const distanceKm = haversineDistance(
    firstCoordinate.lat,
    firstCoordinate.lon,
    lastCoordinate.lat,
    lastCoordinate.lon
  );

  return {
    distanceKm: Number(distanceKm.toFixed(2)),
    distanceType: "straight_line_estimate"
  };
}


// --------------------------------------------------
// LOAD ROUTE DATA
// --------------------------------------------------

function addToStopIndex(stop, route, position) {
  const key = normalizeStop(stop);

  if (!stopIndex.has(key)) {
    stopIndex.set(key, []);
  }

  stopIndex.get(key).push({ route, position });
}

async function loadRouteData() {
  return new Promise((resolve, reject) => {
    if (!fs.existsSync(DATA_FILE)) {
      reject(new Error(`Route dataset not found: ${DATA_FILE}`));
      return;
    }

    const rows = [];

    fs.createReadStream(DATA_FILE)
      .pipe(csv({
        mapHeaders: ({ header }) =>
          header.trim().replace(/^\uFEFF/, "").toLowerCase()
      }))
      .on("data", (row) => {
        const routeName = getField(row, [
          "name",
          "route_name",
          "route_id"
        ]);

        const fullName = getField(row, [
          "full_name",
          "fullname"
        ]);

        const rawStops = getField(row, [
          "stop_list",
          "stops",
          "stop_names"
        ]);

        const stops = parseStopList(rawStops);

        if (stops.length >= 2) {
          rows.push({
            id: rows.length,
            routeName: routeName || `BMTC-${rows.length + 1}`,
            fullName,
            tripCount: Number(getField(row, ["trip_count"]) || 0),
            stops
          });
        }
      })
      .on("end", () => {
        routeData = rows;

        allStops = [
          ...new Set(routeData.flatMap((route) => route.stops))
        ].sort((a, b) => a.localeCompare(b));

        stopIndex = new Map();
        sharedStops = new Set();

        for (const route of routeData) {
          route.stops.forEach((stop, position) => {
            addToStopIndex(stop, route, position);
          });
        }

        for (const [stopKey, occurrences] of stopIndex.entries()) {
          const routeNames = new Set(
            occurrences.map(({ route }) => route.routeName)
          );

          if (routeNames.size > 1) {
            sharedStops.add(stopKey);
          }
        }

        dataLoaded = true;

        console.log(`BMTC dataset loaded: ${routeData.length} routes`);
        console.log(`Unique stop names loaded: ${allStops.length}`);

        resolve();
      })
      .on("error", reject);
  });
}

// --------------------------------------------------
// LOAD STOP COORDINATES
// --------------------------------------------------

async function loadStopCoordinates() {
  return new Promise((resolve, reject) => {
    if (!fs.existsSync(STOPS_FILE)) {
      console.warn(`Coordinate file not found: ${STOPS_FILE}`);
      stopCoordinates = new Map();
      resolve();
      return;
    }

    const coordinates = new Map();
    let rowsRead = 0;

    fs.createReadStream(STOPS_FILE)
      .pipe(csv({
        mapHeaders: ({ header }) =>
          header.trim().replace(/^\uFEFF/, "").toLowerCase()
      }))
      .on("data", (row) => {
        rowsRead++;

        const name = getField(row, [
          "stop_name",
          "stopname",
          "name"
        ]);

        const latValue = getField(row, ["stop_lat"]);
        const lonValue = getField(row, ["stop_lon"]);

        const lat = Number(latValue);
        const lon = Number(lonValue);

        if (
          name &&
          latValue !== "" &&
          lonValue !== "" &&
          Number.isFinite(lat) &&
          Number.isFinite(lon) &&
          (lat !== 0 || lon !== 0) &&
          lat >= -90 &&
          lat <= 90 &&
          lon >= -180 &&
          lon <= 180
        ) {
          const key = normalizeStop(name);

          if (!coordinates.has(key)) {
            coordinates.set(key, { lat, lon });
          }
        }
      })
      .on("end", () => {
        stopCoordinates = coordinates;

        console.log("BMTC coordinate-file rows read:", rowsRead);
        console.log("Valid unique stop coordinates:", coordinates.size);

        resolve();
      })
      .on("error", reject);
  });
}

// --------------------------------------------------
// BUILD A JOURNEY
// --------------------------------------------------



function buildJourney(legs, from, to) {
  const combinedStops = [];

  for (const leg of legs) {
    if (combinedStops.length === 0) {
      combinedStops.push(...leg.stops);
    } else {
      combinedStops.push(...leg.stops.slice(1));
    }
  }

  const transferStops = legs
    .slice(0, -1)
    .map((leg) => leg.to);

  // Calculate distance using the available stop coordinates.
  const distanceResult = calculateJourneyDistance(combinedStops);

  // These are estimates, not live BMTC timings.
  const averageBusSpeedKmph = 18;
  const roadDistanceFactor = 1.3;
  const transferWaitingMinutes = 10;

  let estimatedTravelTimeMinutes = null;

  if (
    distanceResult &&
    Number.isFinite(distanceResult.distanceKm) &&
    distanceResult.distanceKm >= 0
  ) {
    const estimatedRoadDistanceKm =
      distanceResult.distanceKm * roadDistanceFactor;

    estimatedTravelTimeMinutes = Math.ceil(
      (estimatedRoadDistanceKm / averageBusSpeedKmph) * 60 +
      (legs.length - 1) * transferWaitingMinutes
    );
  }

  return {
    routeName: legs.map((leg) => leg.routeName).join(" + "),

    fullName:
      legs.length === 1
        ? `${from} → ${to}`
        : `${from} → ${to} (${legs.length - 1} transfer(s) via ${transferStops.join(", ")})`,

    from,
    to,
    transfers: legs.length - 1,
    stopCount: combinedStops.length,

    ...(distanceResult || {
      distanceKm: null,
      distanceType: "unavailable"
    }),

    estimatedTravelTimeMinutes,

    tripCount:
      legs.length === 1 ? legs[0].tripCount : null,

    stops: combinedStops,

    legs: legs.map((leg) => ({
      routeName: leg.routeName,
      from: leg.from,
      to: leg.to,
      stops: leg.stops
    }))
  };
}



// --------------------------------------------------
// FIND DIRECT AND TRANSFER JOURNEYS
// --------------------------------------------------

function findJourneys(from, to) {
  const fromKey = normalizeStop(from);
  const toKey = normalizeStop(to);

  if (fromKey === toKey) return [];

  const journeys = [];
  const journeyKeys = new Set();

  const MAX_LEGS = 3;
  const MAX_STATES = 5000;
  const MAX_RESULTS = 150;
  const MAX_TRANSFER_CHOICES_PER_ROUTE = 12;

  let visitedStates = 0;

  function saveJourney(legs) {
    if (!legs.length || legs.some(
      (leg) => !leg.stops || leg.stops.length < 2
    )) {
      return;
    }

    for (let i = 0; i < legs.length - 1; i++) {
      if (
        normalizeStop(legs[i].to) !==
        normalizeStop(legs[i + 1].from)
      ) {
        return;
      }
    }

    const journey = buildJourney(legs, from, to);

    const key = journey.stops.map(normalizeStop).join("|");

    if (journeyKeys.has(key)) return;

    journeyKeys.add(key);
    journeys.push(journey);
  }

  function search(currentStop, legs, usedRoutes, visitedTransfers) {
    visitedStates++;

    if (
      visitedStates > MAX_STATES ||
      journeys.length >= MAX_RESULTS
    ) {
      return;
    }

    const currentKey = normalizeStop(currentStop);
    const occurrences = stopIndex.get(currentKey) || [];

    for (const occurrence of occurrences) {
      if (
        visitedStates > MAX_STATES ||
        journeys.length >= MAX_RESULTS
      ) {
        return;
      }

      const { route, position } = occurrence;

      if (usedRoutes.has(route.routeName)) continue;

      const laterStops = route.stops
        .map((stop, index) => ({ stop, index }))
        .filter(({ index }) => index > position);

      const destinationOccurrence = laterStops.find(
        ({ stop }) => normalizeStop(stop) === toKey
      );

      if (destinationOccurrence) {
        saveJourney([
          ...legs,
          {
            routeName: route.routeName,
            from: currentStop,
            to: destinationOccurrence.stop,
            stops: route.stops.slice(
              position,
              destinationOccurrence.index + 1
            ),
            tripCount: route.tripCount
          }
        ]);
      }

      const transferCandidates = laterStops
        .filter(({ stop, index }) => {
          const key = normalizeStop(stop);

          if (
            destinationOccurrence &&
            index >= destinationOccurrence.index
          ) {
            return false;
          }

          return (
            sharedStops.has(key) &&
            key !== currentKey &&
            !visitedTransfers.has(key)
          );
        })
        .slice(0, MAX_TRANSFER_CHOICES_PER_ROUTE);

      if (legs.length + 1 >= MAX_LEGS) continue;

      for (const candidate of transferCandidates) {
        const transferKey = normalizeStop(candidate.stop);

        const nextUsedRoutes = new Set(usedRoutes);
        nextUsedRoutes.add(route.routeName);

        const nextVisitedTransfers = new Set(visitedTransfers);
        nextVisitedTransfers.add(transferKey);

        search(
          candidate.stop,
          [
            ...legs,
            {
              routeName: route.routeName,
              from: currentStop,
              to: candidate.stop,
              stops: route.stops.slice(
                position,
                candidate.index + 1
              ),
              tripCount: route.tripCount
            }
          ],
          nextUsedRoutes,
          nextVisitedTransfers
        );
      }
    }
  }

  // This call MUST stay inside findJourneys().
  search(from, [], new Set(), new Set());

  // Prefer shortest estimated distance. If distance is unavailable,
  // prefer fewer transfers and then fewer stops.
  journeys.sort((a, b) => {
    if (a.distanceKm != null && b.distanceKm == null) return -1;
    if (a.distanceKm == null && b.distanceKm != null) return 1;

    if (
      a.distanceKm != null &&
      b.distanceKm != null &&
      a.distanceKm !== b.distanceKm
    ) {
      return a.distanceKm - b.distanceKm;
    }

    if (a.transfers !== b.transfers) {
      return a.transfers - b.transfers;
    }

    if (a.stopCount !== b.stopCount) {
      return a.stopCount - b.stopCount;
    }

    return a.routeName.localeCompare(b.routeName);
  });

  return journeys;
}



// --------------------------------------------------
// API ENDPOINTS
// All endpoints are outside findJourneys().
// --------------------------------------------------

app.get("/", (req, res) => {
  res.json({
    success: true,
    message: "Sustainable Traveller BMTC API is running"
  });
});

app.get("/api/health", (req, res) => {
  res.json({
    status: "OK",
    service: "BMTC Route Generation",
    datasetExists: fs.existsSync(DATA_FILE),
    coordinateFileExists: fs.existsSync(STOPS_FILE),
    datasetLoaded: dataLoaded,
    routeCount: routeData.length,
    stopCount: allStops.length,
    coordinateCount: stopCoordinates.size
  });
});

app.get("/api/bmtc/stops", (req, res) => {
  if (!dataLoaded) {
    return res.status(503).json({
      success: false,
      message: "BMTC dataset is still loading.",
      stops: []
    });
  }

  res.json({
    success: true,
    count: allStops.length,
    stops: allStops
  });
});

app.get("/api/bmtc/routes", (req, res) => {
  if (!dataLoaded) {
    return res.status(503).json({
      success: false,
      message: "BMTC dataset is not loaded.",
      routes: []
    });
  }

  const requestedFrom = String(req.query.from || "").trim();
  const requestedTo = String(req.query.to || "").trim();

  if (!requestedFrom || !requestedTo) {
    return res.status(400).json({
      success: false,
      message: "Please provide both from and to stop names.",
      routes: []
    });
  }

  const from = resolveStop(requestedFrom);
  const to = resolveStop(requestedTo);

  if (!from || !to) {
    return res.status(404).json({
      success: false,
      message: "One or both stops could not be matched. Select stops from the dropdown list.",
      requestedFrom,
      requestedTo,
      matchedFrom: from,
      matchedTo: to,
      routes: []
    });
  }

  if (normalizeStop(from) === normalizeStop(to)) {
    return res.status(400).json({
      success: false,
      message: "Choose two different stops.",
      routes: []
    });
  }

  const journeys = findJourneys(from, to);
  const bestJourney = journeys[0] || null;
  const recommendations = journeys.slice(1, 25);

  res.json({
    success: true,
    from,
    to,
    count: journeys.length,
    totalFound: journeys.length,
    bestRoute: bestJourney,
    recommendations,
    routes: journeys.slice(0, 25),
    sortOrder: "Shortest estimated geographic distance first; then fewer transfers and stops",
    distanceNote: "Distance is estimated from stop coordinates using straight-line segments, not actual road distance.",
    message: journeys.length
      ? "Journeys sorted by estimated distance. The first journey is the preferred option; the rest are recommendations."
      : "No journey was found in the current dataset for these stops."
  });
});

// --------------------------------------------------
// START SERVER AFTER BOTH FILES ARE LOADED
// --------------------------------------------------

async function startServer() {
  try {
    await loadStopCoordinates();
    await loadRouteData();

    app.listen(PORT, () => {
      console.log(`Backend running at http://localhost:${PORT}`);
      console.log(`Route dataset: ${DATA_FILE}`);
      console.log(`Coordinate dataset: ${STOPS_FILE}`);
    });
  } catch (error) {
    console.error("Failed to load BMTC data:", error.message);
    process.exit(1);
  }
}

startServer();
