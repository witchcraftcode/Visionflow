const API =
  "http://a6126bb5e30104b1689ab6e198168212-1203948690.ap-southeast-2.elb.amazonaws.com";

const API_KEY = "visionflow-demo-key";

export async function predict(file, model = "resnet18") {
  const form = new FormData();
  form.append("file", file);
  form.append("model", model);

  const res = await fetch(`${API}/predict`, {
    method: "POST",
    headers: {
      "X-API-Key": API_KEY,
    },
    body: form,
  });

  if (!res.ok) throw new Error("Prediction failed");

  return res.json();
}

export async function getJob(jobId) {
  const res = await fetch(`${API}/jobs/${jobId}`, {
    headers: {
      "X-API-Key": API_KEY,
    },
  });

  return res.json();
}