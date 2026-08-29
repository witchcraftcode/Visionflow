import { useEffect, useState } from "react";
import { health, metrics } from "../api";

export default function StatsGrid() {
  const [stats, setStats] = useState({
    healthy: "—",
    requests: "—",
    latency: "—",
    queue: "—",
  });

  useEffect(() => {
    async function load() {
      try {
        const h = await health();
        const m = await metrics();

        const text = typeof m === "string" ? m : JSON.stringify(m);

        const extract = (name) => {
          const match = text.match(new RegExp(`${name}.*?([0-9.]+)`));
          return match ? match[1] : "0";
        };

        setStats({
          healthy: h.status === "healthy" ? "Online" : "Offline",
          requests: extract("visionflow_jobs_total"),
          latency: `${extract("visionflow_inference_duration_ms")} ms`,
          queue: extract("visionflow_queue_depth"),
        });
      } catch {
        setStats({
          healthy: "Offline",
          requests: "0",
          latency: "—",
          queue: "—",
        });
      }
    }

    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, []);

  const cards = [
    {
      title: "System Status",
      value: stats.healthy,
      sub: "Health endpoint",
    },
    {
      title: "Completed Jobs",
      value: stats.requests,
      sub: "Prometheus counter",
    },
    {
      title: "Latest Latency",
      value: stats.latency,
      sub: "Worker inference time",
    },
    {
      title: "Queue Depth",
      value: stats.queue,
      sub: "Redis waiting jobs",
    },
  ];

  return (
    <section className="stats-grid">
      {cards.map((c) => (
        <div className="stat-card" key={c.title}>
          <p>{c.title}</p>
          <h2>{c.value}</h2>
          <span>{c.sub}</span>
        </div>
      ))}
    </section>
  );
}