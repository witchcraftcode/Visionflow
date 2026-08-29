import { API_BASE } from "../api";

export default function Navbar() {
  return (
    <nav className="nav">
      <div>
        <h2>VisionFlow</h2>
        <p>Cloud Vision Inference Platform</p>
      </div>

      <div className="links">
        <a href={`${API_BASE}/docs`} target="_blank" rel="noreferrer">Docs</a>
        <a href={`${API_BASE}/metrics`} target="_blank" rel="noreferrer">Metrics</a>
        <a href="https://github.com/witchcraftcode/Visionflow" target="_blank" rel="noreferrer">
          GitHub
        </a>
      </div>
    </nav>
  );
}