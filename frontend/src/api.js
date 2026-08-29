import axios from "axios";

const api = axios.create({
  baseURL:
    "http://a6126bb5e30104b1689ab6e198168212-1203948690.ap-southeast-2.elb.amazonaws.com",
  headers: {
    "X-API-Key": "visionflow-demo-key",
  },
});

export const predict = async (file, model = "resnet18") => {
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

export const metrics = async () => {
  const { data } = await api.get("/metrics");
  return data;
};