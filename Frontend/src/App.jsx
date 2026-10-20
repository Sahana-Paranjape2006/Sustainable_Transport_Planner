
import { Fragment, useEffect, useMemo, useState } from "react";
import {
  ArrowDownUp,
  ArrowRight,
  Bus,
  CheckCircle2,
  ChevronDown,
  Clock,
  Leaf,
  LoaderCircle,
  MapPin,
  Navigation,
  Search,
  Signpost,
  Sparkles,
  XCircle,
} from "lucide-react";
import "./App.css";

const API_BASE = "http://localhost:5000/api/bmtc";

function normalizeStop(item) {
  if (typeof item === "string") return item.trim();

  if (item && typeof item === "object") {
    return String(
      item.stop_name ??
        item.stopName ??
        item.name ??
        item.label ??
        ""
    ).trim();
  }

  return "";
}

function App() {
  const [stops, setStops] = useState([]);
  const [fromStop, setFromStop] = useState("");
  const [toStop, setToStop] = useState("");
  const [routes, setRoutes] = useState([]);
  const [loadingStops, setLoadingStops] = useState(true);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState("");
  const [searched, setSearched] = useState(false);
  const [expandedRoute, setExpandedRoute] = useState(null);

  useEffect(() => {
    async function loadStops() {
      try {
        setLoadingStops(true);
        setError("");

        const response = await fetch(`${API_BASE}/stops`);

        if (!response.ok) {
          throw new Error("Could not load bus stops from the backend.");
        }

        const data = await response.json();

        const stopList = Array.isArray(data)
          ? data
          : data.stops ?? data.data ?? [];

        const uniqueStops = [
          ...new Set(stopList.map(normalizeStop).filter(Boolean)),
        ].sort((a, b) => a.localeCompare(b));

        if (uniqueStops.length === 0) {
          throw new Error(
            "No stops were found. Check the /api/bmtc/stops API."
          );
        }

        setStops(uniqueStops);
      } catch (err) {
        setError(
          `${err.message} Make sure the backend is running at localhost:5000.`
        );
      } finally {
        setLoadingStops(false);
      }
    }

    loadStops();
  }, []);

  // Sort routes by estimated distance, then transfers, then stop count.
  // Routes with unknown distances are placed after routes with known distances.
  const sortedRoutes = useMemo(() => {
    return [...routes].sort((a, b) => {
      const distanceA =
        a.distanceKm != null && Number.isFinite(Number(a.distanceKm))
          ? Number(a.distanceKm)
          : null;

      const distanceB =
        b.distanceKm != null && Number.isFinite(Number(b.distanceKm))
          ? Number(b.distanceKm)
          : null;

      if (distanceA === null && distanceB !== null) return 1;
      if (distanceA !== null && distanceB === null) return -1;

      if (distanceA !== null && distanceB !== null) {
        if (distanceA !== distanceB) return distanceA - distanceB;
      }

      const transfersA = Number(a.transfers ?? 0);
      const transfersB = Number(b.transfers ?? 0);

      if (transfersA !== transfersB) {
        return transfersA - transfersB;
      }

      return Number(a.stopCount ?? a.stops?.length ?? 0) -
        Number(b.stopCount ?? b.stops?.length ?? 0);
    });
  }, [routes]);

  function swapStops() {
    setFromStop(toStop);
    setToStop(fromStop);
    setRoutes([]);
    setSearched(false);
    setError("");
    setExpandedRoute(null);
  }

  async function searchRoutes(event) {
    event.preventDefault();

    if (!fromStop.trim() || !toStop.trim()) {
      setError("Please enter both your starting stop and destination.");
      return;
    }

    if (fromStop.trim().toLowerCase() === toStop.trim().toLowerCase()) {
      setError("Please select two different bus stops.");
      return;
    }

    try {
      setSearching(true);
      setError("");
      setSearched(false);
      setRoutes([]);
      setExpandedRoute(null);

      const params = new URLSearchParams({
        from: fromStop.trim(),
        to: toStop.trim(),
      });

      const response = await fetch(
        `${API_BASE}/routes?${params.toString()}`
      );

      if (!response.ok) {
        throw new Error("Unable to search routes. Please try again.");
      }

      const data = await response.json();

      const foundRoutes = Array.isArray(data)
        ? data
        : data.routes ?? [];

      setRoutes(foundRoutes);
      setSearched(true);

      if (foundRoutes.length === 0) {
        setError(
          data.message ||
            "No matching route was found. Try different stops."
        );
      }
    } catch (err) {
      setError(
        `${err.message} Check that the backend is running and accessible.`
      );
    } finally {
      setSearching(false);
    }
  }

  function resetSearch() {
    setFromStop("");
    setToStop("");
    setRoutes([]);
    setSearched(false);
    setError("");
    setExpandedRoute(null);
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a
          className="brand"
          href="#home"
          aria-label="Sustainable Traveller home"
        >
          <span className="brand-icon">
            <Leaf size={23} />
          </span>
          <span>
            <strong>Sustainable Traveller</strong>
            <small>Smarter journeys, greener cities</small>
          </span>
        </a>

        <div className="header-tag">
          <span className="status-dot" />
          BMTC route planner
        </div>
      </header>

      <main id="home">
        <section className="hero">
          <div className="hero-copy">
            <div className="eyebrow">
              <Sparkles size={15} />
              YOUR JOURNEY, REIMAGINED
            </div>

            <h1>
              Travel smarter.
              <br />
              <span>Leave a lighter footprint.</span>
            </h1>

            <p>
              Find BMTC bus routes between stops in Bengaluru and plan
              your next journey with public transport.
            </p>

            <div className="hero-points">
              <span>
                <CheckCircle2 size={17} /> Route discovery
              </span>
              <span>
                <CheckCircle2 size={17} /> Stop-by-stop details
              </span>
              <span>
                <CheckCircle2 size={17} /> Public transport first
              </span>
            </div>
          </div>

          <div className="hero-art" aria-hidden="true">
            <div className="art-circle circle-one" />
            <div className="art-circle circle-two" />
            <div className="art-leaf leaf-one">
              <Leaf size={54} />
            </div>
            <div className="art-leaf leaf-two">
              <Leaf size={34} />
            </div>
            <div className="art-bus">
              <Bus size={90} strokeWidth={1.35} />
            </div>
            <div className="art-road" />
            <span className="art-pin pin-one">
              <MapPin size={21} />
            </span>
            <span className="art-pin pin-two">
              <MapPin size={21} />
            </span>
          </div>
        </section>

        <section className="planner-section">
          <div className="section-heading">
            <div>
              <span className="section-kicker">PLAN YOUR TRIP</span>
              <h2>Where would you like to go?</h2>
              <p>Choose your starting stop and your destination.</p>
            </div>

            <div className="heading-icon">
              <Navigation size={25} />
            </div>
          </div>

          <form className="search-card" onSubmit={searchRoutes}>
            <div className="stop-field">
              <label htmlFor="from-stop">FROM</label>
              <div className="input-wrap">
                <span className="field-icon origin-icon">
                  <MapPin size={19} />
                </span>

                <input
                  id="from-stop"
                  list="bmtc-stop-options"
                  value={fromStop}
                  onChange={(event) => {
                    setFromStop(event.target.value);
                    setRoutes([]);
                    setSearched(false);
                    setError("");
                  }}
                  placeholder={
                    loadingStops
                      ? "Loading bus stops..."
                      : "Type or select starting stop"
                  }
                  autoComplete="off"
                  disabled={loadingStops || stops.length === 0}
                />
              </div>
            </div>

            <button
              className="swap-button"
              type="button"
              onClick={swapStops}
              aria-label="Swap starting stop and destination"
              title="Swap stops"
            >
              <ArrowDownUp size={19} />
            </button>

            <div className="stop-field">
              <label htmlFor="to-stop">TO</label>
              <div className="input-wrap">
                <span className="field-icon destination-icon">
                  <MapPin size={19} />
                </span>

                <input
                  id="to-stop"
                  list="bmtc-stop-options"
                  value={toStop}
                  onChange={(event) => {
                    setToStop(event.target.value);
                    setRoutes([]);
                    setSearched(false);
                    setError("");
                  }}
                  placeholder="Type or select destination"
                  autoComplete="off"
                  disabled={loadingStops || stops.length === 0}
                />
              </div>
            </div>

            <button
              className="search-button"
              type="submit"
              disabled={searching || loadingStops || stops.length === 0}
            >
              {searching ? (
                <LoaderCircle className="spin" size={19} />
              ) : (
                <Search size={19} />
              )}
              {searching ? "Searching..." : "Find routes"}
              {!searching && <ArrowRight size={17} />}
            </button>

            <datalist id="bmtc-stop-options">
              {stops.map((stop) => (
                <option key={stop} value={stop} />
              ))}
            </datalist>
          </form>

          <div className="planner-footnote">
            <span>
              <CheckCircle2 size={15} />
              {loadingStops
                ? "Loading stop information..."
                : `${stops.length.toLocaleString()} stop names loaded from your dataset`}
            </span>

            <button
              className="text-button"
              type="button"
              onClick={resetSearch}
            >
              <XCircle size={15} />
              Clear search
            </button>
          </div>

          {error && (
            <div className="notice" role="alert">
              <XCircle size={19} />
              <span>{error}</span>
            </div>
          )}
        </section>

        {searched && sortedRoutes.length > 0 && (
          <section className="results-section">
            <div className="results-heading">
              <div>
                <span className="section-kicker">YOUR MATCHES</span>
                <h2>Routes for your journey</h2>
                <p>
                  <strong>{fromStop}</strong>
                  <ArrowRight size={15} />
                  <strong>{toStop}</strong>
                </p>
              </div>

              <div className="result-count">
                <strong>{sortedRoutes.length}</strong>
                <span>matching routes</span>
              </div>
            </div>

            <div className="results-list">
              {sortedRoutes.map((route, index) => {
                const routeKey =
                  route.routeName ??
                  route.route_id ??
                  `route-${index}`;

                const routeStops = Array.isArray(route.stops)
                  ? route.stops.map(normalizeStop).filter(Boolean)
                  : [];

                const isExpanded = expandedRoute === routeKey;

                const distanceKm =
                  route.distanceKm != null &&
                  Number.isFinite(Number(route.distanceKm))
                    ? Number(route.distanceKm)
                    : null;

                return (
                  <Fragment key={`${routeKey}-${index}`}>
                    {index === 0 && (
                      <h2 className="results-section-title">
                        Best Route for Your Journey
                      </h2>
                    )}

                    {index === 1 && (
                      <h2 className="results-section-title">
                        Recommended Alternatives
                      </h2>
                    )}

                    <article className="route-card">
                      <div className="route-card-top">
                        <div className="route-symbol">
                          <Bus size={23} />
                        </div>

                        <div className="route-title">
                          <span className="route-number">
                            {route.routeName ??
                              route.route_id ??
                              "BMTC route"}
                          </span>

                          {index === 0 && (
                            <span className="best-route-label">
                              <CheckCircle2 size={14} />
                              Best estimated-distance match
                            </span>
                          )}

                          <h3>
                            {route.from || fromStop} →{" "}
                            {route.to || toStop}
                          </h3>

                          {Array.isArray(route.legs) &&
                            route.legs.length > 0 && (
                              <div className="route-legs">
                                {route.legs.map((leg, legIndex) => (
                                  <div
                                    className="route-leg"
                                    key={`${leg.routeName}-${legIndex}`}
                                  >
                                    <span className="leg-number">
                                      {legIndex + 1}
                                    </span>
                                    <div>
                                      <strong>{leg.routeName}</strong>
                                      <p>
                                        {leg.from} → {leg.to}
                                      </p>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            )}
                        </div>

                        <button
                          className="details-button"
                          type="button"
                          onClick={() =>
                            setExpandedRoute(
                              isExpanded ? null : routeKey
                            )
                          }
                        >
                          {isExpanded ? "Hide stops" : "View stops"}
                          <ChevronDown
                            size={17}
                            className={
                              isExpanded ? "rotate-chevron" : ""
                            }
                          />
                        </button>
                      </div>

                      <div className="route-metrics">
                        <div>
                          <Signpost size={17} />
                          <span>
                            <strong>
                              {route.stopCount ?? routeStops.length}
                            </strong>{" "}
                            stops listed
                          </span>
                        </div>

                        <div>
                          <Navigation size={17} />
                          <span>
                            {distanceKm !== null ? (
                              <>
                                <strong>
                                  {distanceKm.toFixed(2)} km
                                </strong>{" "}
                                estimated straight-line distance
                              </>
                            ) : (
                              "Distance unavailable"
                            )}
                          </span>
                        </div>

                        {route.transfers != null && (
                          <div>
                            <ArrowDownUp size={17} />
                            <span>
                              <strong>{route.transfers}</strong>{" "}
                              transfers
                            </span>
                          </div>
                        )}

                        {route.tripCount != null && (
                          <div>
                            <Bus size={17} />
                            <span>
                              <strong>{route.tripCount}</strong>{" "}
                              dataset trip records
                            </span>
                          </div>
                        )}
                      </div>

                      {isExpanded && (
                        <div className="stop-details">
                          <h4>Stops listed for this route</h4>

                          {routeStops.length > 0 ? (
                            <ol className="stop-list">
                              {routeStops.map((stop, stopIndex) => (
                                <li key={`${stop}-${stopIndex}`}>
                                  <span className="stop-number">
                                    {stopIndex + 1}
                                  </span>
                                  <span>{stop}</span>
                                </li>
                              ))}
                            </ol>
                          ) : (
                            <p className="empty-stops">
                              No stop sequence was returned for this route.
                            </p>
                          )}
                        </div>
                      )}
                    </article>
                  </Fragment>
                );
              })}
            </div>

            <p className="data-note">
              <Clock size={15} />
              Results use the available dataset. Distance is an estimated
              straight-line distance, not actual road distance. Live arrival
              times, current traffic, and real-time crowd levels are not
              provided by this route API.
            </p>
          </section>
        )}

        {!searched && !loadingStops && (
          <section className="feature-grid">
            <div className="feature-card">
              <span className="feature-icon green">
                <Bus size={22} />
              </span>
              <h3>Discover bus routes</h3>
              <p>
                Find routes that match your selected origin and destination.
              </p>
            </div>

            <div className="feature-card">
              <span className="feature-icon blue">
                <Signpost size={22} />
              </span>
              <h3>Explore the stops</h3>
              <p>
                Open a route to review the stop sequence returned by the API.
              </p>
            </div>

            <div className="feature-card">
              <span className="feature-icon orange">
                <Leaf size={22} />
              </span>
              <h3>Travel more sustainably</h3>
              <p>
                Use public transport as one option for lower-impact travel.
              </p>
            </div>
          </section>
        )}

        <footer className="footer">
          <div className="footer-brand">
            <Leaf size={17} />
            Sustainable Traveller
          </div>
          <p>
            Built for smarter, more sustainable journeys in Bengaluru.
          </p>
        </footer>
      </main>
    </div>
  );
}

export default App;
