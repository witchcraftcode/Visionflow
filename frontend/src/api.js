import axios from "axios";

// Same Vercel deployment serves both the frontend and /api/* — no separate
// backend URL or CORS config needed for the default setup.
export const API_BASE = import.meta.env.VITE_API_URL || "/api";

const api = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
});

export const health = async () => (await api.get("/health")).data;

export const metrics = async () => (await api.get("/metrics")).data;

export const predict = async (file, model) => {
  const form = new FormData();
  form.append("file", file);
  form.append("model", model);
  return (await api.post("/predict", form)).data;
};