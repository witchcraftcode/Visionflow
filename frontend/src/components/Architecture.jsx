import { ArrowRight, Boxes, Cloud, Database, HardDrive, Layers3, Server } from "lucide-react";

const pipeline = [
  { label: "React", detail: "Vite dashboard", icon: Layers3, tone: "blue" },
  { label: "FastAPI", detail: "Async API", icon: Server, tone: "green" },
  { label: "Redis", detail: "Job queue", icon: Boxes, tone: "red" },
  { label: "Worker Pods", detail: "Kubernetes", icon: Cloud, tone: "orange" },
];

const storage = [
  { label: "PostgreSQL", detail: "Model registry", icon: Database },
  { label: "S3", detail: "Image artifacts", icon: HardDrive },
];

export default function Architecture() {
  return (
    <div className="architecture-diagram">
      <div className="pipeline-row">
        {pipeline.map((node, index) => {
          const Icon = node.icon;
          return (
            <div className="pipeline-node-wrap" key={node.label}>
              <article className={`pipeline-node tone-${node.tone}`}>
                <Icon size={22} />
                <strong>{node.label}</strong>
                <span>{node.detail}</span>
              </article>
              {index < pipeline.length - 1 && (
                <div className="pipeline-arrow" aria-hidden="true">
                  <ArrowRight size={18} />
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="storage-branch">
        {storage.map((node) => {
          const Icon = node.icon;
          return (
            <article className="storage-node" key={node.label}>
              <Icon size={21} />
              <div>
                <strong>{node.label}</strong>
                <span>{node.detail}</span>
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}
