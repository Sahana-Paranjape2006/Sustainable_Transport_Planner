const fs = require("fs");
const path = require("path");

const DATA_PATH = path.join(
  __dirname,
  "..",
  "data",
  "processed",
  "metro",
  "metro_network.csv"
);

// Load processed Metro CSV
function loadMetroNetwork() {
  if (!fs.existsSync(DATA_PATH)) {
    throw new Error(`Metro CSV not found: ${DATA_PATH}`);
  }

  const content = fs.readFileSync(DATA_PATH, "utf8").trim();
  const lines = content.split(/\r?\n/);

  if (lines.length < 2) {
    throw new Error("Metro CSV contains no station data.");
  }

  const headers = lines[0]
    .replace(/^\uFEFF/, "")
    .split(",")
    .map(header => header.trim());

  return lines.slice(1).map(line => {
    const values = line.split(",");
    const row = {};

    headers.forEach((header, index) => {
      row[header] = (values[index] || "").trim();
    });

    return row;
  });
}

// Build a weighted graph of Metro stations
function buildMetroGraph(rows) {
  const graph = new Map();
  const stations = new Map();

  for (const row of rows) {
    const code = row.station_code;
    if (!code) continue;

    const latitude = Number(row.latitude);
    const longitude = Number(row.longitude);

    stations.set(code, {
      station_code: code,
      station_name: row.station_name,
      line: row.line,
      is_interchange: row.is_interchange,
      latitude,
      longitude
    });

    if (!graph.has(code)) {
      graph.set(code, []);
    }
  }

  for (const row of rows) {
    const from = row.station_code;
    const to = row.next_station_code;

    if (!from || !to || from === to) continue;
    if (!stations.has(from) || !stations.has(to)) continue;

    const distance = Number(row.distance_to_next_km);

    // Do not silently use missing or invalid distances
    if (!Number.isFinite(distance) || distance <= 0) {
      continue;
    }

    graph.get(from).push({
      station_code: to,
      distance_km: distance
    });

    // Treat connections as bidirectional for this prototype.
    // Validate this assumption against the source data.
    graph.get(to).push({
      station_code: from,
      distance_km: distance
    });
  }

  return { graph, stations };
}

// Dijkstra's algorithm: find minimum-distance route
function findMetroRoute(startCode, destinationCode) {
  const rows = loadMetroNetwork();
  const { graph, stations } = buildMetroGraph(rows);

  if (!stations.has(startCode)) {
    throw new Error(`Starting station not found: ${startCode}`);
  }

  if (!stations.has(destinationCode)) {
    throw new Error(`Destination station not found: ${destinationCode}`);
  }

  const distances = new Map();
  const previous = new Map();
  const unvisited = new Set(graph.keys());

  for (const code of unvisited) {
    distances.set(code, Infinity);
  }

  distances.set(startCode, 0);

  while (unvisited.size > 0) {
    let current = null;
    let smallestDistance = Infinity;

    for (const code of unvisited) {
      const distance = distances.get(code);

      if (distance < smallestDistance) {
        smallestDistance = distance;
        current = code;
      }
    }

    // No remaining reachable stations
    if (current === null) break;

    if (current === destinationCode) break;

    unvisited.delete(current);

    for (const edge of graph.get(current) || []) {
      if (!unvisited.has(edge.station_code)) continue;

      const candidateDistance =
        distances.get(current) + edge.distance_km;

      if (candidateDistance < distances.get(edge.station_code)) {
        distances.set(edge.station_code, candidateDistance);

        previous.set(edge.station_code, {
          from: current,
          distance_km: edge.distance_km
        });
      }
    }
  }

  if (distances.get(destinationCode) === Infinity) {
    return {
      found: false,
      message: "No route found between these stations."
    };
  }

  // Reconstruct route
  const routeCodes = [];
  let current = destinationCode;

  while (current !== startCode) {
    routeCodes.unshift(current);

    const step = previous.get(current);

    if (!step) {
      return {
        found: false,
        message: "Unable to reconstruct the route."
      };
    }

    current = step.from;
  }

  routeCodes.unshift(startCode);

  const route = routeCodes.map(code => stations.get(code));

  return {
    found: true,
    algorithm: "Dijkstra",
    total_stations: route.length,
    total_distance_km: Number(
      distances.get(destinationCode).toFixed(2)
    ),
    route
  };
}

module.exports = {
  loadMetroNetwork,
  buildMetroGraph,
  findMetroRoute
};