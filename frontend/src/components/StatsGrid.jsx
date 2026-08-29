import { useEffect, useState } from "react";
import { health, metrics, parseMetric } from "../api";
import {
  Activity,
  Gauge,
  Database,
  CheckCircle,
} from "lucide-react";

export default function StatsGrid() {
  const [stats, setStats] = useState({
    online: "Checking",
    jobs: "0",
    latency: "0",
    queue: "0",
  });

  async function loadStats() {
    try {
      const h = await health();
      const m = await metrics();

      setStats({
        online: h.status === "ok" ? "Online" : "Offline",
        jobs: parseMetric(m, "visionflow_jobs_total"),
        latency: parseMetric(
          m,
          "visionflow_inference_duration_ms"
        ),
        queue: parseMetric(m, "visionflow_queue_depth"),
      });
    } catch (e) {
      setStats({
        online: "Offline",
        jobs: "0",
        latency: "0",
        queue: "0",
      });
    }
  }

  useEffect(() => {
    loadStats();

    const timer = setInterval(loadStats, 5000);

    return () => clearInterval(timer);
  }, []);

  const cards = [
    {
      title: "System Status",
      value: stats.online,
      sub: "FastAPI Health",
      icon: <CheckCircle size={26} />,
    },
    {
      title: "Completed Jobs",
      value: stats.jobs,
      sub: "Prometheus Counter",
      icon: <Database size={26} />,
    },
    {
      title: "Latest Latency",
      value: `${stats.latency} ms`,
      sub: "Worker Inference",
      icon: <Gauge size={26} />,
    },
    {
      title: "Queue Depth",
      value: stats.queue,
      sub: "Redis Waiting Jobs",
      icon: <Activity size={26} />,
    },
  ];

  return (
    <section className="stats-grid">
      {cards.map((card) => (
        <div className="stat-card" key={card.title}>
          <div className="stat-icon">{card.icon}</div>

          <p>{card.title}</p>

          <h2>{card.value}</h2>

          <span>{card.sub}</span>
        </div>
      ))}
    </section>
  );
}