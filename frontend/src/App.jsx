import { useCallback, useEffect, useMemo, useState } from "react";
import { Activity, AlertCircle, CheckCircle2, Clock, Server } from "lucide-react";

import {
  fetchHealth,
  fetchMetrics,
  parsePrometheusMetrics,
  pollJob,
  runPrediction,
} from "./api";
import Architecture from "./components/Architecture";
import ModelRegistry from "./components/ModelRegistry";
import Navbar from "./components/Navbar";
import PredictionResult from "./components/PredictionResult";
import StatsGrid from "./components/StatsGrid";
import UploadPanel from "./components/UploadPanel";

import "./styles.css";

const TERMINAL_FAILURES = new Set(["failed", "timed_out", "dead_lettered"]);

const MODELS = [
  {
    id: "resnet18",
    name: "ResNet18",
    task: "Image classification",
    description: "Balanced accuracy and latency for general visual recognition.",
    badge: "Default",
    accent: "blue",
  },
  {
    id: "mobilenet",
    name: "MobileNet",
    task: "Edge-optimized CNN",
    description: "Lightweight inference path for fast turnaround and lower compute.",
    badge: "Fast",
    accent: "green",
  },
  {
    id: "yolov5",
    name: "YOLOv5",
    task: "Object detection",
    description: "Detection model for localizing multiple objects in uploaded images.",
    badge: "Detect",
    accent: "orange",
  },
];

const initialTelemetry = {
  isLoading: true,
  healthStatus: "unknown",
  requests: 0,
  latencyMs: null,
  queueDepth: 0,
  updatedAt: null,
};

function normalizeResult(job, selectedModel, fileName) {
  const rawResult = Array.isArray(job?.result) ? job.result[0] : job?.result;
  const detections = rawResult?.detections || job?.detections || [];
  const bestDetection = Array.isArray(detections) ? detections[0] : null;
  const confidenceRaw =
    rawResult?.confidence ?? bestDetection?.confidence ?? job?.confidence ?? 0;
  const confidence = Number(confidenceRaw) <= 1 ? Number(confidenceRaw) * 100 : Number(confidenceRaw);
  const label =
    rawResult?.label ??
    bestDetection?.label ??
    bestDetection?.class_name ??
    bestDetection?.class_id ??
    job?.label ??
    "Prediction ready";

  return {
    jobId: job?.job_id,
    status: job?.status,
    label: String(label),
    confidence: Number.isFinite(confidence) ? confidence : 0,
    inferenceTimeMs:
      job?.duration_ms ??
      job?.inference_latency_ms ??
      job?.latency_ms ??
      rawResult?.duration_ms ??
      null,
    model: job?.model || selectedModel,
    modelVersion: job?.model_version,
    filename: fileName,
    detections,
    completedAt: new Date().toISOString(),
  };
}

export default function App() {
  const [selectedModel, setSelectedModel] = useState("resnet18");
  const [file, setFile] = useState(null);
  const [telemetry, setTelemetry] = useState(initialTelemetry);
  const [job, setJob] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [recentJobs, setRecentJobs] = useState([]);

  const isProcessing = ["uploading", "queued", "processing"].includes(job?.status);
  const activeModel = MODELS.find((model) => model.id === selectedModel) || MODELS[0];
  const previewUrl = useMemo(() => (file ? URL.createObjectURL(file) : ""), [file]);

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const loadTelemetry = useCallback(async () => {
    try {
      const [health, metricsText] = await Promise.all([fetchHealth(), fetchMetrics()]);
      const parsed = parsePrometheusMetrics(metricsText);

      setTelemetry({
        isLoading: false,
        healthStatus: health?.status || "unknown",
        requests: parsed.httpRequests,
        latencyMs: parsed.averageLatencyMs,
        queueDepth: parsed.queueDepth ?? health?.queue_depth ?? 0,
        updatedAt: new Date().toISOString(),
      });
    } catch {
      setTelemetry((current) => ({
        ...current,
        isLoading: false,
        healthStatus: "offline",
        updatedAt: new Date().toISOString(),
      }));
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react/set-state-in-effect
    loadTelemetry();
    const timer = window.setInterval(loadTelemetry, 5000);
    return () => window.clearInterval(timer);
  }, [loadTelemetry]);

  const handleRunInference = async () => {
    if (!file || isProcessing) return;

    setError("");
    setResult(null);
    setJob({ status: "uploading" });

    try {
      const queued = await runPrediction(file, selectedModel);
      setJob(queued);

      const completedJob = await pollJob(queued.job_id, (nextJob) => {
        setJob(nextJob);
      });

      if (TERMINAL_FAILURES.has(completedJob.status)) {
        throw new Error(completedJob.error || completedJob.message || "Inference failed.");
      }

      const normalized = normalizeResult(completedJob, selectedModel, file.name);
      setJob(completedJob);
      setResult(normalized);
      setRecentJobs((jobs) => [normalized, ...jobs].slice(0, 5));
      loadTelemetry();
    } catch (runError) {
      const message =
        runError?.response?.data?.error?.message ||
        runError?.response?.data?.detail?.reason ||
        runError?.message ||
        "Unable to run inference.";
      setError(message);
      setJob((current) => ({ ...(current || {}), status: "failed" }));
    }
  };

  const stats = useMemo(
    () => [
      {
        label: "System Status",
        value: telemetry.healthStatus === "ok" ? "Operational" : "Degraded",
        detail: telemetry.isLoading ? "Checking health" : "Health endpoint",
        icon: CheckCircle2,
        tone: telemetry.healthStatus === "ok" ? "success" : "danger",
      },
      {
        label: "HTTP Requests",
        value: telemetry.requests.toLocaleString(),
        detail: "Prometheus counter",
        icon: Activity,
        tone: "blue",
      },
      {
        label: "Average Latency",
        value: telemetry.latencyMs == null ? "--" : `${telemetry.latencyMs.toFixed(1)} ms`,
        detail: "Request latency",
        icon: Clock,
        tone: "amber",
      },
      {
        label: "Queue Depth",
        value: String(telemetry.queueDepth ?? 0),
        detail: "Redis jobs pending",
        icon: Server,
        tone: "violet",
      },
    ],
    [telemetry],
  );

  return (
    <div className="app-shell">
      <Navbar />

      <main>
        <section className="hero section-band" id="dashboard">
          <div className="hero-copy">
            <div className={`live-badge ${telemetry.healthStatus === "ok" ? "is-live" : ""}`}>
              <span />
              {telemetry.healthStatus === "ok" ? "Live production API" : "API health degraded"}
            </div>
            <h1>VisionFlow</h1>
            <p>Cloud-Native ML Vision Inference Platform</p>
          </div>

          <div className="hero-console" aria-label="Live inference pipeline">
            <div className="console-top">
              <span />
              <span />
              <span />
            </div>
            <code>POST /predict</code>
            <strong>{activeModel.name}</strong>
            <p>Queued inference, Kubernetes workers, Prometheus telemetry.</p>
          </div>
        </section>

        <StatsGrid stats={stats} />

        <section className="section-band" id="models">
          <div className="section-heading">
            <p>Model Registry</p>
            <h2>Select a deployed vision model</h2>
          </div>
          <ModelRegistry models={MODELS} selectedModel={selectedModel} onSelectModel={setSelectedModel} />
        </section>

        <section className="workspace-grid section-band" id="api">
          <UploadPanel
            file={file}
            selectedModel={activeModel}
            isProcessing={isProcessing}
            status={job?.status}
            onFileSelect={setFile}
            onRunInference={handleRunInference}
          />

          <PredictionResult
            error={error}
            file={file}
            job={job}
            previewUrl={previewUrl}
            recentJobs={recentJobs}
            result={result}
          />
        </section>

        {error && (
          <section className="error-card section-band" role="alert">
            <AlertCircle size={20} />
            <div>
              <h3>Inference failed</h3>
              <p>{error}</p>
            </div>
          </section>
        )}

        <section className="section-band" id="architecture">
          <div className="section-heading">
            <p>Architecture</p>
            <h2>Asynchronous inference pipeline</h2>
          </div>
          <Architecture />
        </section>
      </main>
    </div>
  );
}
