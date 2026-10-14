import { useState } from "react";
import "./App.css";

function App() {
  const [start, setStart] = useState("KGWA");
  const [destination, setDestination] = useState("RVR");
  const [startLine, setStartLine] = useState("Purple Line");
  const [destinationLine, setDestinationLine] = useState("Yellow Line");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function findRoute(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const params = new URLSearchParams({
        start,
        destination,
        startLine,
        destinationLine,
      });

      const response = await fetch(
        `http://localhost:5001/api/metro/route?${params}`
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Unable to find the route.");
      }

      if (!data.found) {
        throw new Error("No route found for these stations.");
      }

      setResult(data);
    } catch (err) {
      setError(err.message || "Could not connect to the Metro API.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page">
      <header className="header">
        <div className="brand">GO<span>GREEN</span></div>
        <p>SUSTAINABLE TRANSPORT PLANNER</p>
        <h1>Your city. A greener journey.</h1>
        <p className="subtitle">
          Plan metro journeys with estimated travel time, distance and transfers.
        </p>
      </header>

      <section className="planner">
        <h2>Plan your metro journey</h2>

        <form onSubmit={findRoute}>
          <label>
            Starting station code
            <input
              value={start}
              onChange={(e) => setStart(e.target.value.toUpperCase())}
              placeholder="e.g. KGWA"
              required
            />
          </label>

          <label>
            Starting line
            <select
              value={startLine}
              onChange={(e) => setStartLine(e.target.value)}
            >
              <option>Purple Line</option>
              <option>Green Line</option>
              <option>Yellow Line</option>
            </select>
          </label>

          <label>
            Destination station code
            <input
              value={destination}
              onChange={(e) =>
                setDestination(e.target.value.toUpperCase())
              }
              placeholder="e.g. RVR"
              required
            />
          </label>

          <label>
            Destination line
            <select
              value={destinationLine}
              onChange={(e) => setDestinationLine(e.target.value)}
            >
              <option>Yellow Line</option>
              <option>Purple Line</option>
              <option>Green Line</option>
            </select>
          </label>

          <button type="submit" disabled={loading}>
            {loading ? "Finding route..." : "Find my route"}
          </button>
        </form>

        <p className="hint">
          Try KGWA (Majestic), Purple Line → RVR (Rashtreeya Vidyalaya Road),
          Yellow Line.
        </p>

        {error && <p className="error">{error}</p>}

        {result && (
          <section className="results">
            <h2>Your suggested route</h2>

            <div className="stats">
              <div>
                <strong>{result.total_distance_km} km</strong>
                <span>Rail distance</span>
              </div>
              <div>
                <strong>{result.estimated_travel_time_min} min</strong>
                <span>Estimated time</span>
              </div>
              <div>
                <strong>{result.transfers}</strong>
                <span>Transfers</span>
              </div>
            </div>

            <h3>Stations along the way</h3>
            <ol className="route-list">
              {result.route.map((station, index) => (
                <li key={`${station.node_id}-${index}`}>
                  <div>
                    <strong>{station.station_name}</strong>
                    <span>
                      {station.line} · {station.station_code}
                    </span>
                  </div>
                  {station.connection_from_previous === "transfer" && (
                    <span className="transfer">Change line</span>
                  )}
                </li>
              ))}
            </ol>

            <p className="disclaimer">
              Travel time is an estimate based on assumed metro speed and
              transfer time. It is not live timetable information.
            </p>
          </section>
        )}
      </section>

      <footer>Choose public transport. Move towards a greener Bengaluru.</footer>
    </main>
  );
}

export default App;