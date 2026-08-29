export default function PredictionCard({ result, model, status, jobId }) {
  if (!result) return null;

  const confidence = Number(result.confidence);

  return (
    <section className="prediction-card">
      <div className="prediction-header">
        <div>
          <p className="muted">Prediction</p>
          <h2>{result.label}</h2>
        </div>

        <span className="success-badge">{status}</span>
      </div>

      <div className="confidence-section">
        <div className="confidence-row">
          <span>Confidence</span>
          <strong>{confidence.toFixed(2)}%</strong>
        </div>

        <div className="progress">
          <div
            className="progress-fill"
            style={{ width: `${Math.min(confidence, 100)}%` }}
          />
        </div>
      </div>

      <div className="meta-grid">
        <div>
          <span>Model</span>
          <h4>{model}</h4>
        </div>

        <div>
          <span>Job Status</span>
          <h4>{status}</h4>
        </div>

        <div className="full-width">
          <span>Job ID</span>
          <code>{jobId}</code>
        </div>
      </div>
    </section>
  );
}