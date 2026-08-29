import { useEffect, useState } from "react";
import { health, metrics } from "../api";

export default function StatsGrid() {
  const [stats, setStats] = useState({
    status: "Loading",
    requests: "0",
    latency: "--",
  });

  useEffect(() => {
    const load = async () => {
      try {
        const h = await health();
        const m = await metrics();

        setStats({
          status: h.status === "ok" ? "Online" : "Offline",
          requests: String(m.requests_total ?? 0),
          latency: Number(m.avg_latency_ms ?? 0).toFixed(1),
        });
      } catch {
        setStats({
          status: "Offline",
          requests: "0",
          latency: "--",
        });
      }
    };

    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, []);

  const cards = [
    ["System Status", stats.status],
    ["Requests (this instance)", stats.requests],
    ["Avg Latency", `${stats.latency} ms`],
    ["Deployment", "Vercel Serverless"],
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
