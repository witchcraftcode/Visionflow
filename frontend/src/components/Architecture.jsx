import {
  Globe,
  Database,
  Server,
  Cpu,
  HardDrive,
  ArrowRight,
} from "lucide-react";

export default function Architecture() {
  const nodes = [
    { icon: Globe, name: "React UI", color: "#2563eb" },
    { icon: Server, name: "FastAPI", color: "#0ea5e9" },
    { icon: Database, name: "Redis Queue", color: "#dc2626" },
    { icon: Cpu, name: "Worker Pods", color: "#7c3aed" },
    { icon: HardDrive, name: "RDS Registry", color: "#059669" },
  ];

  return (
    <section className="architecture-card">
      <div className="section-title">
        <h2>Production Architecture</h2>
        <p>End-to-end inference pipeline running on Kubernetes</p>
      </div>

      <div className="pipeline">
        {nodes.map((node, index) => {
          const Icon = node.icon;

          return (
            <div className="pipeline-node" key={node.name}>
              <div
                className="icon-circle"
                style={{ background: `${node.color}20`, color: node.color }}
              >
                <Icon size={28} />
              </div>

              <h4>{node.name}</h4>

              {index !== nodes.length - 1 && (
                <ArrowRight className="arrow" size={18} />
              )}
            </div>
          );
        })}
      </div>

      <div className="infra-grid">
        <div>
          <span>Container Orchestration</span>
          <h3>Amazon EKS</h3>
        </div>

        <div>
          <span>Object Storage</span>
          <h3>Amazon S3</h3>
        </div>

        <div>
          <span>Database</span>
          <h3>PostgreSQL RDS</h3>
        </div>

        <div>
          <span>Queue Broker</span>
          <h3>Redis</h3>
        </div>
      </div>
    </section>
  );
}