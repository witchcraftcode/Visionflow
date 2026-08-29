import { FileText, Activity } from "lucide-react";

const ELB =
  (import.meta.env.VITE_API_URL ||
    "http://a6126bb5e30104b1689ab6e198168212-1203948690.ap-southeast-2.elb.amazonaws.com") + "/api/v1";

export default function Navbar() {
  return (
    <nav className="nav">
      <div className="logo">VisionFlow</div>

      <div className="links">
        <a href={`${ELB}/docs`} target="_blank" rel="noreferrer">
          <FileText size={16}/> Docs
        </a>

        <a href={`${ELB}/metrics`} target="_blank" rel="noreferrer">
          <Activity size={16}/> Metrics
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