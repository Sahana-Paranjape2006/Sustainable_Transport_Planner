const {
  loadMetroNetwork,
  findMetroRoute
} = require("./metro_route_engine");

try {
  const rows = loadMetroNetwork();

  // Select stations from the actual CSV
  const stations = [
    ...new Map(
      rows
        .filter(row => row.station_code && row.station_name)
        .map(row => [row.station_code, row])
    ).values()
  ];

  if (stations.length < 3) {
    throw new Error("Not enough stations for testing.");
  }

  // Use the first and third stations in the dataset
  const start = stations[0];
  const destination = stations[2];

  console.log("Starting station:", start.station_name);
  console.log("Destination station:", destination.station_name);

  const result = findMetroRoute(
    start.station_code,
    destination.station_code
  );

  if (result.found) {
    console.log("\nRoute found!");
    console.log("Total stations:", result.total_stations);
    console.log("Algorithm:", result.algorithm);
    console.log("Total distance:", result.total_distance_km, "km");

    console.log("\nStation-by-station route:");
    result.route.forEach((station, index) => {
      console.log(`${index + 1}. ${station.station_name}`);
    });
  } else {
    console.log(result.message);
  }
} catch (error) {
  console.error("Test failed:", error.message);
}