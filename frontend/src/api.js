import axios from "axios";

export const API_BASE =
  import.meta.env.VITE_API_URL ||
  "http://a6126bb5e30104b1689ab6e198168212-1203948690.ap-southeast-2.elb.amazonaws.com";

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    "X-API-Key": "visionflow-demo-key",
  },
});

export const health = async () => (await api.get("/health")).data;
export const metrics = async () =>
  (await api.get("/metrics", { responseType: "text" })).data;
export const predict = async (file, model) => {
  const form = new FormData();
  form.append("file", file);
  form.append("model", model);
  return (await api.post("/predict", form)).data;
};
export const getJob = async (id) => (await api.get(`/jobs/${id}`)).data;