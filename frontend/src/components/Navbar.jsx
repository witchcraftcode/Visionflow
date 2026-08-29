import { API_BASE } from "../api";

export default function Navbar() {
  return (
    <nav className="nav">
      <a href={`${API_BASE}/docs`} target="_blank" rel="noreferrer">Docs</a>
      <a href={`${API_BASE}/metrics`} target="_blank" rel="noreferrer">Metrics</a>
      <a href="https://github.com/witchcraftcode/Visionflow" target="_blank" rel="noreferrer">GitHub</a>
    </nav>
  );
}