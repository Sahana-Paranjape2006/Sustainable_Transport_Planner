Metro Route Engine API

Purpose

Calculates an estimated Bengaluru Metro route between two stations using Dijkstra's algorithm.

Endpoint

"GET /api/metro/route"

Query parameters

Parameter| Required| Example
"start"| Yes| "KGWA"
"destination"| Yes| "RVR"
"startLine"| When needed to identify the starting line| "Purple Line"
"destinationLine"| When needed to identify the destination line| "Yellow Line"

Example request

"http://localhost:5001/api/metro/route?start=KGWA&destination=RVR&startLine=Purple%20Line&destinationLine=Yellow%20Line"

Successful response

- "found": Whether a route was found
- "algorithm": Route-finding algorithm
- "total_stations": Number of station nodes in the returned route
- "total_distance_km": Estimated rail distance in kilometres
- "estimated_travel_time_min": Estimated travel time in minutes
- "transfers": Number of line transfers
- "assumptions": Estimated speed and transfer time
- "route": Ordered station nodes, including station codes, names, lines, coordinates and connection types

Error handling

Missing required station codes return HTTP 400 with an error message. Check "found" and the response status before displaying route results.

Current assumptions

Average metro speed: 30 km/h. Transfer time: 5 minutes. These are prototype assumptions, not live operational timings.

Integration

The frontend can request a route from this endpoint. Other modules can use the route's station sequence and distance for further calculations. The emissions module must use an agreed comparison baseline before calculating emissions savings.