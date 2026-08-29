import { Clock, CheckCircle2, Loader2, XCircle, Brain } from "lucide-react";

export default function PredictionCard({
  result,
  status,
  jobId,
  model,
  latency,
  file,
}) {
  const confidence = result
    ? Number(result.confidence).toFixed(2)
    : 0;

  const progress =
    status === "Completed"
      ? 100
      : status === "Processing"
      ? 70
      : status === "Queued"
      ? 35
      : 0;

  const StatusIcon = () => {
    if (status === "Completed")
      return <CheckCircle2 size={18} color="#22c55e" />;

    if (
      status === "Queued" ||
      status === "Uploading" ||
      status === "Processing"
    )
      return <Loader2 size={18} className="spin" color="#60a5fa" />;

    if (status === "Failed")
      return <XCircle size={18} color="#ef4444" />;

    return <Clock size={18} color="#94a3b8" />;
  };

  return (
    <div className="result-card">
      <h2>Prediction Result</h2>

      <div className="status-pill">
        <StatusIcon />
        <span>{status}</span>
      </div>

      {file && (
        <div className="result-image">
          <img src={URL.createObjectURL(file)} alt="uploaded" />
        </div>
      )}

      {!result ? (
        <div className="empty-result">
          <Brain size={44} />

          <h3>Waiting for inference</h3>

          <p>
            Upload an image and run inference to receive the prediction,
            confidence score, latency and job metadata.
          </p>
        </div>
      ) : (
        <>
          <div className="result-main">
            <p className="label-title">Top Prediction</p>

            <h1>{result.label}</h1>

            <div className="confidence">{confidence}% confidence</div>

            <div className="progress">
              <div
                className="progress-fill"
                style={{ width: `${confidence}%` }}
              />
            </div>
          </div>

          <div className="meta">
            <div className="meta-row">
              <span>Model</span>
              <strong>{model}</strong>
            </div>

            <div className="meta-row">
              <span>Latency</span>
              <strong>{latency ?? "--"} ms</strong>
            </div>

            <div className="meta-row">
              <span>Job ID</span>
              <strong className="job-id">
                {jobId ? `${jobId.slice(0, 8)}...` : "--"}
              </strong>
            </div>

            <div className="meta-row">
              <span>Status</span>
              <strong>{status}</strong>
            </div>
          </div>
        </>
      )}

      {!result && (
        <div className="progress">
          <div
            className="progress-fill processing"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}
    </div>
  );
}