import axios from "axios";

/* ---------- API Base ---------- */

export const API_BASE =
  import.meta.env.VITE_API_URL ||
  "http://a6126bb5e30104b1689ab6e198168212-1203948690.ap-southeast-2.elb.amazonaws.com";

/* ---------- Axios Client ---------- */

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    "X-API-Key": "visionflow-demo-key",
  },
  timeout: 60000,
});

/* ---------- Health ---------- */

export async function health() {
  const { data } = await api.get("/health");
  return data;
}

/* ---------- Prometheus Metrics ---------- */

export async function metrics() {
  const { data } = await api.get("/metrics", {
    responseType: "text",
  });
  return data;
}

/* ---------- Submit Inference ---------- */

export async function predict(file, model) {
  const form = new FormData();

  form.append("file", file);
  form.append("model", model);

  const { data } = await api.post("/predict", form);

  return data;
}

/* ---------- Poll Job ---------- */

export async function getJob(jobId) {
  const { data } = await api.get(`/jobs/${jobId}`);
  return data;
}

/* ---------- Metrics Parser ---------- */

export function parseMetric(text, metricName) {
  if (!text) return "0";

  const match = text.match(
    new RegExp(`${metricName}\\s+([0-9.]+)`)
  );

  return match ? match[1] : "0";
}

export default api;