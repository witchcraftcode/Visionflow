import axios from "axios";

export const API_BASE_URL = (
  import.meta.env.VITE_API_URL ||
  "http://a6126bb5e30104b1689ab6e198168212-1203948690.ap-southeast-2.elb.amazonaws.com/api/v1"
).replace(/\/$/, "");

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
});

const sleep = (ms) => new Promise((resolve) => window.setTimeout(resolve, ms));

export async function fetchHealth() {
  const response = await api.get("/health");
  return response.data;
}

export async function fetchMetrics() {
  const response = await api.get("/metrics", {
    responseType: "text",
    transformResponse: [(data) => data],
  });
  return response.data || "";
}

export async function runPrediction(file, model) {
  const form = new FormData();
  form.append("file", file);
  form.append("model", model);

  const response = await api.post("/predict", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

export async function fetchJob(jobId) {
  const response = await api.get(`/jobs/${jobId}`);
  return response.data;
}

export async function pollJob(jobId, onUpdate) {
  let currentJob = await fetchJob(jobId);
  onUpdate?.(currentJob);

  while (!["completed", "failed", "timed_out", "dead_lettered"].includes(currentJob.status)) {
    await sleep(2000);
    currentJob = await fetchJob(jobId);
    onUpdate?.(currentJob);
  }

  return currentJob;
}

export function parsePrometheusMetrics(text) {
  const series = {};

  String(text)
    .split("\n")
    .forEach((line) => {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("#")) return;

      const match = trimmed.match(/^([a-zA-Z_:][a-zA-Z0-9_:]*)(?:\{[^}]*\})?\s+(-?\d+(?:\.\d+)?(?:e[+-]?\d+)?)$/i);
      if (!match) return;

      const [, name, rawValue] = match;
      const value = Number(rawValue);
      if (!Number.isFinite(value)) return;

      series[name] = (series[name] || 0) + value;
    });

  const latencyAvgSeconds = series.visionflow_http_request_latency_seconds_avg;
  const latencySumSeconds = series.visionflow_http_request_latency_seconds_sum;
  const latencyCount = series.visionflow_http_request_latency_seconds_count;
  const averageLatencyMs =
    latencyAvgSeconds != null
      ? latencyAvgSeconds * 1000
      : latencySumSeconds != null && latencyCount
        ? (latencySumSeconds / latencyCount) * 1000
        : null;

  return {
    httpRequests: Math.round(series.visionflow_http_requests_total || 0),
    averageLatencyMs,
    queueDepth: Math.round(series.visionflow_queue_depth || 0),
    failedRequests: Math.round(series.visionflow_failed_requests_total || 0),
  };
}
