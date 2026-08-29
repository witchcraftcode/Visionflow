import { API_BASE } from "../api";
import { Github, FileText, Activity } from "lucide-react";

export default function Navbar() {
  return (
    <nav className="nav">
      <div className="logo">
        <div className="logo-dot" />
        <span>VisionFlow</span>
      </div>

      <div className="nav-links">
        <a
          href={`${API_BASE}/docs`}
          target="_blank"
          rel="noreferrer"
        >
          <FileText size={18} />
          Docs
        </a>

        <a
          href={`${API_BASE}/metrics`}
          target="_blank"
          rel="noreferrer"
        >
          <Activity size={18} />
          Metrics
        </a>

        <a
          href="https://github.com/witchcraftcode/Visionflow"
          target="_blank"
          rel="noreferrer"
        >
          <Github size={18} />
          GitHub
        </a>
      </div>
    </nav>
  );
}