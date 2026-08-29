import { Activity, ExternalLink, Gauge, Layers, Network, Workflow } from "lucide-react";
import { API_BASE_URL } from "../api";

const navItems = [
  { label: "Dashboard", href: "#dashboard", icon: Gauge },
  { label: "Architecture", href: "#architecture", icon: Network },
  { label: "Models", href: "#models", icon: Layers },
  { label: "API", href: "#api", icon: Workflow },
];

export default function Navbar() {
  return (
    <header className="navbar">
      <a className="brand" href="#dashboard" aria-label="VisionFlow dashboard">
        <span className="brand-mark">VF</span>
        <span>VisionFlow</span>
      </a>

      <nav className="nav-links" aria-label="Primary navigation">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <a key={item.label} href={item.href}>
              <Icon size={16} />
              {item.label}
            </a>
          );
        })}
      </nav>

      <div className="nav-actions">
        <a className="icon-button" href={`${API_BASE_URL}/metrics`} target="_blank" rel="noreferrer">
          <Activity size={16} />
          Metrics
        </a>
        <a
          className="icon-button secondary"
          href="https://github.com/witchcraftcode/Visionflow"
          target="_blank"
          rel="noreferrer"
        >
          <ExternalLink size={16} />
          GitHub
        </a>
      </div>
    </header>
  );
}
