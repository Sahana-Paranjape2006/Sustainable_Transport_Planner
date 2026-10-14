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

// Configurable prototype assumptions; validate before real-world use.
const AVERAGE_SPEED_KMH = 30;
const TRANSFER_TIME_MIN = 5;

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
    .map(value => value.trim());

  return lines.slice(1).map(line => {
    const values = line.split(",");
    const row = {};

    headers.forEach((header, index) => {
      row[header] = (values[index] || "").trim();
    });

    return row;
  });
}

function makeNodeId(code, line) {
  return `${code}__${line.trim().toLowerCase()}`;
}

function buildMetroGraph(rows) {
  const graph = new Map();
  const stations = new Map();
  const nodesByCode = new Map();
  const rowsByCodeAndLine = new Map();

  // Create one node for each station on each Metro line.
  for (const row of rows) {
    if (!row.station_code || !row.line) continue;

    const code = row.station_code;
    const line = row.line.trim();
    const nodeId = makeNodeId(code, line);

    const station = {
      node_id: nodeId,
      station_code: code,
      station_name: row.station_name,
      line,
      is_interchange: row.is_interchange,
      latitude: Number(row.latitude),
      longitude: Number(row.longitude)
    };

    stations.set(nodeId, station);

    if (!graph.has(nodeId)) graph.set(nodeId, []);

    if (!nodesByCode.has(code)) nodesByCode.set(code, []);
    if (!nodesByCode.get(code).includes(nodeId)) {
      nodesByCode.get(code).push(nodeId);
    }

    rowsByCodeAndLine.set(`${code}__${line.toLowerCase()}`, row);
  }

  function addEdge(from, to, edge) {
    graph.get(from).push({ to, ...edge });
  }

  // Add track connections along the same line.
  for (const row of rows) {
    if (!row.station_code || !row.next_station_code || !row.line) {
      continue;
    }

    const line = row.line.trim();
    const from = makeNodeId(row.station_code, line);
    const to = makeNodeId(row.next_station_code, line);

    // Do not connect to a station on a different line by mistake.
    if (!stations.has(from) || !stations.has(to)) continue;

    const distance = Number(row.distance_to_next_km);

    if (!Number.isFinite(distance) || distance <= 0) continue;

    const travelTimeMin = (distance / AVERAGE_SPEED_KMH) * 60;

    // Trains travel in both directions on a connected track segment.
    addEdge(from, to, {
      type: "rail",
      distance_km: distance,
      time_min: travelTimeMin
    });

    addEdge(to, from, {
      type: "rail",
      distance_km: distance,
      time_min: travelTimeMin
    });
  }

  // Connect line-specific nodes at interchange stations.
  for (const [code, nodeIds] of nodesByCode) {
    if (nodeIds.length < 2) continue;

    const interchange = nodeIds.every(
      id => stations.get(id).is_interchange === "1"
    );

    if (!interchange) continue;

    for (let i = 0; i < nodeIds.length; i++) {
      for (let j = i + 1; j < nodeIds.length; j++) {
        const first = nodeIds[i];
        const second = nodeIds[j];

        addEdge(first, second, {
          type: "transfer",
          distance_km: 0,
          time_min: TRANSFER_TIME_MIN
        });

        addEdge(second, first, {
          type: "transfer",
          distance_km: 0,
          time_min: TRANSFER_TIME_MIN
        });
      }
    }
  }

  return { graph, stations, nodesByCode };
}

function findMetroRoute(
  startCode,
  destinationCode,
  startLine = null,
  destinationLine = null
) {
  const rows = loadMetroNetwork();
  const { graph, stations, nodesByCode } = buildMetroGraph(rows);

  function resolveNode(code, line) {
    const candidates = nodesByCode.get(code) || [];

    if (line) {
      return candidates.find(id =>
        stations.get(id).line.toLowerCase() === line.toLowerCase()
      );
    }

    // For interchange stations, specify a line to remove ambiguity.
    return candidates.length === 1 ? candidates[0] : undefined;
  }

  const start = resolveNode(startCode, startLine);
  const destination = resolveNode(destinationCode, destinationLine);

  if (!start) {
    throw new Error(
      `Starting station "${startCode}" not found or ambiguous. Specify its line.`
    );
  }

  if (!destination) {
    throw new Error(
      `Destination "${destinationCode}" not found or ambiguous. Specify its line.`
    );
  }

  const distances = new Map();
  const previous = new Map();
  const unvisited = new Set(graph.keys());

  for (const node of unvisited) distances.set(node, Infinity);
  distances.set(start, 0);

  while (unvisited.size > 0) {
    let current = null;
    let best = Infinity;

    for (const node of unvisited) {
      if (distances.get(node) < best) {
        best = distances.get(node);
        current = node;
      }
    }

    if (current === null) break;
    if (current === destination) break;

    unvisited.delete(current);

    for (const edge of graph.get(current) || []) {
      if (!unvisited.has(edge.to)) continue;

      const candidate = distances.get(current) + edge.time_min;

      if (candidate < distances.get(edge.to)) {
        distances.set(edge.to, candidate);
        previous.set(edge.to, {
          from: current,
          edge
        });
      }
    }
  }

  if (!Number.isFinite(distances.get(destination))) {
    return {
      found: false,
      message: "No route found between these stations."
    };
  }

  const steps = [];
  let current = destination;

  while (current !== start) {
    const step = previous.get(current);

    if (!step) {
      return {
        found: false,
        message: "Unable to reconstruct the route."
      };
    }

    steps.unshift({
      station: stations.get(current),
      connection: step.edge
    });

    current = step.from;
  }

  const route = [
    {
      ...stations.get(start),
      connection_from_previous: null
    },
    ...steps.map(step => ({
      ...step.station,
      connection_from_previous: step.connection.type
    }))
  ];

  const totalDistanceKm = steps.reduce(
    (sum, step) => sum + step.connection.distance_km,
    0
  );

  const transferCount = steps.filter(
    step => step.connection.type === "transfer"
  ).length;

  return {
    found: true,
    algorithm: "Dijkstra (estimated travel time)",
    total_stations: route.length,
    total_distance_km: Number(totalDistanceKm.toFixed(2)),
    estimated_travel_time_min: Number(
      distances.get(destination).toFixed(1)
    ),
    transfers: transferCount,
    assumptions: {
      average_speed_kmh: AVERAGE_SPEED_KMH,
      transfer_time_min: TRANSFER_TIME_MIN
    },
    route
  };
}

module.exports = {
  loadMetroNetwork,
  buildMetroGraph,
  findMetroRoute
};