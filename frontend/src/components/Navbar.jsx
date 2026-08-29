import { FileText, Activity } from "lucide-react";

export default function Navbar() {
  return (
    <nav className="nav">
      <div className="logo">VisionFlow</div>

      <div className="links">
        <a href="/api/docs" target="_blank" rel="noreferrer">
          <FileText size={16} /> Docs
        </a>

        <a href="/api/metrics" target="_blank" rel="noreferrer">
          <Activity size={16} /> Metrics
        </a>

        <a
          href="https://github.com/witchcraftcode/Visionflow"
          target="_blank"
          rel="noreferrer"
        >
          GitHub
        </a>
      </div>
    </nav>
  );
}
