import {
  Globe,
  Cloud,
  Server,
  Database,
  Cpu,
  Workflow,
  ArrowRight,
} from "lucide-react";

const nodes = [
  {
    title: "Browser",
    sub: "Vercel React",
    icon: <Globe size={28} />,
    color: "#2563eb",
  },
  {
    title: "Load Balancer",
    sub: "AWS ALB",
    icon: <Cloud size={28} />,
    color: "#7c3aed",
  },
  {
    title: "FastAPI",
    sub: "Async API",
    icon: <Server size={28} />,
    color: "#0ea5e9",
  },
  {
    title: "Redis",
    sub: "Job Queue",
    icon: <Workflow size={28} />,
    color: "#f59e0b",
  },
  {
    title: "Worker",
    sub: "ONNX Runtime",
    icon: <Cpu size={28} />,
    color: "#10b981",
  },
  {
    title: "PostgreSQL",
    sub: "Model Registry",
    icon: <Database size={28} />,
    color: "#ec4899",
  },
];

export default function Architecture() {
  return (
    <div className="architecture-wrapper">
      <div className="architecture">
        {nodes.map((node, index) => (
          <div className="pipeline-step" key={node.title}>
            <div className="node">
              <div
                className="node-icon"
                style={{ background: `${node.color}22`, color: node.color }}
              >
                {node.icon}
              </div>

              <h4>{node.title}</h4>

              <p>{node.sub}</p>
            </div>

            {index !== nodes.length - 1 && (
              <div className="arrow">
                <ArrowRight size={18} />
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="architecture-info">
        <div className="info-card">
          <h3>Asynchronous Inference</h3>

          <p>
            The full project queues images in Redis and processes them on a
            separate ONNX worker, with metadata stored in PostgreSQL — see the
            diagram above.
          </p>
        </div>

        <div className="info-card">
          <h3>Production Stack</h3>

          <ul>
            <li>FastAPI + Uvicorn</li>
            <li>Redis Queue</li>
            <li>Kubernetes (EKS)</li>
            <li>PostgreSQL (RDS)</li>
            <li>ONNX Runtime</li>
            <li>Prometheus Metrics</li>
          </ul>
        </div>

        <div className="info-card">
          <h3>This Live Demo</h3>

          <p>
            Runs on Vercel only, with no card required: the frontend is a
            static build, and prediction runs as one Python serverless
            function that loads the ONNX model and returns a result directly
            — no Redis, worker, or database. Same models, same preprocessing,
            simpler request path.
          </p>
        </div>
      </div>
    </div>
  );
}