import { useState } from "react";
import { predict, getJob } from "./api";
import "./App.css";

export default function App() {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("");
  const [result, setResult] = useState(null);

  async function handlePredict() {
    if (!file) return;

    setStatus("Uploading...");
    setResult(null);

    const job = await predict(file);

    setStatus("Processing...");

    const timer = setInterval(async () => {
      const data = await getJob(job.job_id);

      if (data.status === "completed") {
        clearInterval(timer);
        setStatus("Completed");
        setResult(data.result);
      }

      if (data.status === "dead_lettered") {
        clearInterval(timer);
        setStatus("Failed");
      }
    }, 1000);
  }

  return (
    <div className="container">
      <h1>VisionFlow</h1>
      <p>Cloud-native ML Vision Inference Platform</p>

      <input
        type="file"
        accept="image/*"
        onChange={(e) => setFile(e.target.files[0])}
      />

      <button onClick={handlePredict}>Predict</button>

      <h3>{status}</h3>

      {result && (
        <div className="card">
          <h2>Prediction</h2>
          <p>Label: {result.label}</p>
          <p>Confidence: {result.confidence.toFixed(2)}%</p>
        </div>
      )}
    </div>
  );
}