import { Activity } from "lucide-react";
import { API_BASE } from "../api";

export default function Navbar() {
  return (
    <nav className="nav">
      <div className="logo">VisionFlow</div>

      <div className="nav-links">
        <a href={`${API_BASE}/metrics`} target="_blank" rel="noreferrer">
          <Activity size={16}/>
          Metrics
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