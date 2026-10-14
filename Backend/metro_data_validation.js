const { loadMetroNetwork } = require("./metro_route_engine");

const rows = loadMetroNetwork();

const requiredFields = [
  "station_code",
  "station_name",
  "line",
  "sequence",
  "latitude",
  "longitude"
];

const stationCodes = new Set();
const duplicateCodes = new Set();
const missingFields = [];
const invalidDistances = [];
const unknownConnections = [];

for (const row of rows) {
  // Check required fields
  for (const field of requiredFields) {
    if (!row[field]) {
      missingFields.push({
        station: row.station_name || "Unknown",
        field
      });
    }
  }

  // Detect duplicate station codes.
  // These may be valid for interchange stations.
  if (stationCodes.has(row.station_code)) {
    duplicateCodes.add(row.station_code);
  }

  stationCodes.add(row.station_code);

  // Validate distance when a next station exists
  if (row.next_station_code) {
    const distance = Number(row.distance_to_next_km);

    if (!Number.isFinite(distance) || distance <= 0) {
      invalidDistances.push({
        station: row.station_name,
        distance: row.distance_to_next_km
      });
    }
  }
}

// Check whether each next station exists on the same line
for (const row of rows) {
  if (!row.next_station_code) continue;

  const connectionExists = rows.some(
    candidate =>
      candidate.station_code === row.next_station_code &&
      candidate.line === row.line
  );

  if (!connectionExists) {
    unknownConnections.push({
      station: row.station_name,
      next_station_code: row.next_station_code,
      line: row.line
    });
  }
}

console.log("\n===== METRO DATA VALIDATION =====");
console.log("Total CSV rows:", rows.length);
console.log("Unique station codes:", stationCodes.size);
console.log("Duplicate station codes:", [...duplicateCodes]);
console.log("Missing required fields:", missingFields);
console.log("Invalid distances:", invalidDistances);
console.log("Unknown connections:", unknownConnections);

console.log("\n===== VALIDATION SUMMARY =====");

if (
  missingFields.length === 0 &&
  invalidDistances.length === 0 &&
  unknownConnections.length === 0
) {
  console.log("Required fields, distances and connections passed.");
} else {
  console.log("Issues found. Review the details above.");
}

console.log(
  "Note: Duplicate codes can be valid when stations serve multiple lines."
);