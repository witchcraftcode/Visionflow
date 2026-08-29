import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL;

const api = axios.create({
  baseURL: API_URL,
  headers: {
    "X-API-Key": "visionflow-demo-key",
  },
});

export const predict = async (file, model) => {
  const form = new FormData();
  form.append("file", file);
  form.append("model", model);

  const { data } = await api.post("/predict", form);
  return data;
};

export const getJob = async (jobId) => {
  const { data } = await api.get(`/jobs/${jobId}`);
  return data;
};

export const health = async () => {
  const { data } = await api.get("/health");
  return data;
};

export const API_BASE = API_URL;