import { AlertTriangle, CheckCircle2, Clock3, History, Loader2, Sparkles } from "lucide-react";

function formatConfidence(value) {
  const safeValue = Number.isFinite(Number(value)) ? Number(value) : 0;
  return `${Math.max(0, Math.min(100, safeValue)).toFixed(1)}%`;
}

function formatTime(ms) {
  if (ms == null) return "--";
  return `${Number(ms).toFixed(0)} ms`;
}

export default function PredictionResult({ error, file, job, previewUrl, recentJobs, result }) {
  const isProcessing = ["uploading", "queued", "processing"].includes(job?.status);
  const isFailed = Boolean(error) || job?.status === "failed";
  const statusLabel = job?.status || "idle";

  return (
    <section className="tool-panel result-panel">
      <div className="panel-heading row-heading">
        <div>
          <p>Prediction Result</p>
          <h2>Live job output</h2>
        </div>
        <span className={`status-pill ${result ? "success" : isFailed ? "danger" : ""}`}>
          {isProcessing && <Loader2 className="spin" size={15} />}
          {result && <CheckCircle2 size={15} />}
          {isFailed && <AlertTriangle size={15} />}
          {!isProcessing && !result && !isFailed && <Clock3 size={15} />}
          {result ? "completed" : statusLabel}
        </span>
      </div>

      {previewUrl ? (
        <div className="image-preview">
          <img alt={file?.name || "Uploaded preview"} src={previewUrl} />
        </div>
      ) : (
        <div className="empty-result">
          <Sparkles size={34} />
          <h3>Awaiting an image</h3>
          <p>Choose a model, upload an image, and run inference.</p>
        </div>
      )}

      {isFailed && (
        <div className="inline-error">
          <AlertTriangle size={18} />
          <p>{error || "The worker returned a failed status."}</p>
        </div>
      )}

      {result && (
        <div className="prediction-output">
          <div className="prediction-main">
            <span>Predicted label</span>
            <strong>{result.label}</strong>
            <p>{formatConfidence(result.confidence)} confidence</p>
            <div className="confidence-track">
              <span style={{ width: formatConfidence(result.confidence) }} />
            </div>
          </div>

          <div className="result-meta-grid">
            <div>
              <span>Inference time</span>
              <strong>{formatTime(result.inferenceTimeMs)}</strong>
            </div>
            <div>
              <span>Model used</span>
              <strong>{result.model}</strong>
            </div>
            <div>
              <span>Status</span>
              <strong className="success-text">Success</strong>
            </div>
            <div>
              <span>Job ID</span>
              <strong>{result.jobId?.slice(0, 8) || "--"}</strong>
            </div>
          </div>
        </div>
      )}

      <div className="recent-jobs">
        <div className="recent-heading">
          <History size={17} />
          <h3>Recent Jobs</h3>
        </div>

        {recentJobs.length === 0 ? (
          <p className="recent-empty">Completed inferences will appear here.</p>
        ) : (
          <div className="recent-list">
            {recentJobs.map((recentJob) => (
              <div className="recent-job" key={`${recentJob.jobId}-${recentJob.completedAt}`}>
                <div>
                  <strong>{recentJob.filename}</strong>
                  <span>{recentJob.model}</span>
                </div>
                <div className="recent-job-meta">
                  <span>{formatConfidence(recentJob.confidence)}</span>
                  <em>completed</em>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
