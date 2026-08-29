export default function Navbar() {
  return (
    <nav className="navbar">
      <div className="brand">
        <h2>VisionFlow</h2>
        <span>Cloud Vision Inference Platform</span>
      </div>

      <div className="nav-links">
        <a href="/docs" target="_blank">Docs</a>
        <a href="/metrics" target="_blank">Metrics</a>
        <a
          href="https://github.com/witchcraftcode/Visionflow"
          target="_blank"
        >
          GitHub
        </a>
      </div>
    </nav>
  );
}