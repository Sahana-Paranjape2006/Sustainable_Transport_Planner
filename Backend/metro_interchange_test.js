const { findMetroRoute } = require("./metro_route_engine");

try {
  const result = findMetroRoute(
    "KGWA",
    "RVR",
    "Purple Line",
    "Yellow Line"
  );

  if (!result.found) {
    console.log(result.message);
    process.exitCode = 1;
  } else {
    console.log("\n===== METRO ROUTE SUMMARY =====");
    console.log("Algorithm:", result.algorithm);
    console.log("Rail distance:", result.total_distance_km, "km");
    console.log(
      "Estimated time:",
      result.estimated_travel_time_min,
      "minutes"
    );
    console.log("Line changes:", result.transfers);

    console.log("\nJourney:");

    for (let i = 0; i < result.route.length; i++) {
      const station = result.route[i];

      if (station.connection_from_previous === "transfer") {
        console.log(`  CHANGE LINE at ${station.station_name}`);
      }

      console.log(
        `${i + 1}. ${station.station_name} (${station.line})`
      );
    }
  }
} catch (error) {
  console.error("Test failed:", error.message);
  process.exitCode = 1;
}