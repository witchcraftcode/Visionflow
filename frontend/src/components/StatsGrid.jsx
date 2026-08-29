import { useEffect, useState } from "react";
import { health, metrics } from "../api";

export default function StatsGrid() {
  const [stats, setStats] = useState({
    status: "Loading",
    requests: "0",
    latency: "--",
    queue: "0",
  });

  useEffect(() => {
    const load = async () => {
      try {
        const h = await health();
        const m = await metrics();

        const get = (name) => {
          const r = new RegExp(`${name}[^\\n]* ([0-9.]+)`);
          const match = m.match(r);
          return match ? match[1] : "0";
        };

        setStats({
          status: h.status === "ok" ? "Online" : "Offline",
          requests: get("visionflow_http_requests_total"),
          latency: Number(
            get("visionflow_http_request_latency_seconds_avg") * 1000
          ).toFixed(1),
          queue: get("visionflow_queue_depth"),
        });
      } catch {
        setStats({
          status: "Offline",
          requests: "0",
          latency: "--",
          queue: "0",
        });
      }
    };

    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, []);

  const cards = [
    ["System Status", stats.status],
    ["HTTP Requests", stats.requests],
    ["Avg Latency", `${stats.latency} ms`],
    ["Queue Depth", stats.queue],
  ];

  return (
    <section className="stats-grid">
      {cards.map(([title, value]) => (
        <div className="stat-card" key={title}>
          <p>{title}</p>
          <h2>{value}</h2>
        </div>
      ))}
    </section>
  );
}