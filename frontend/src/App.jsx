import { useState } from "react";
import { predict, getJob } from "./api";

import Navbar from "./components/Navbar";
import StatsGrid from "./components/StatsGrid";
import ModelSelector from "./components/ModelSelector";
import UploadCard from "./components/UploadCard";
import PredictionCard from "./components/PredictionCard";
import Architecture from "./components/Architecture";

import "./App.css";

export default function App() {
  const [file, setFile] = useState(null);
  const [selectedModel, setSelectedModel] = useState("resnet18");
  const [status, setStatus] = useState("Idle");
  const [result, setResult] = useState(null);
  const [jobId, setJobId] = useState("");
  const [latency, setLatency] = useState(null);

  const handlePredict = async () => {
    if (!file) {
      alert("Please upload an image first.");
      return;
    }

    setResult(null);
    setLatency(null);
    setStatus("Uploading");

    try {
      const start = performance.now();

      const job = await predict(file, selectedModel);

      setJobId(job.job_id);
      setStatus("Queued");

      const timer = setInterval(async () => {
        const data = await getJob(job.job_id);

        if (data.status === "processing") {
          setStatus("Processing");
        }

        if (data.status === "completed") {
          clearInterval(timer);

          setLatency(Math.round(performance.now() - start));
          setResult(data.result);
          setStatus("Completed");
        }

        if (data.status === "dead_lettered") {
          clearInterval(timer);
          setStatus("Failed");
        }
      }, 1000);
    } catch (err) {
      console.error(err);
      setStatus("Error");
    }
  };

  return (
    <div className="app">
      <Navbar />

      <main className="container">
        <section className="hero">
          <h1>VisionFlow</h1>
          <p>Cloud-Native ML Vision Inference Platform</p>
        </section>

        <StatsGrid />

        <section className="section">
          <div className="section-title">
            <h2>Model Registry</h2>
            <p>Select the deployed model for inference</p>
          </div>

          <ModelSelector
            selected={selectedModel}
            setSelected={setSelectedModel}
          />
        </section>

        <section className="dashboard-grid">
          <UploadCard
            file={file}
            setFile={setFile}
            selectedModel={selectedModel}
            onPredict={handlePredict}
            status={status}
          />

          <PredictionCard
            result={result}
            status={status}
            jobId={jobId}
            model={selectedModel}
            latency={latency}
            file={file}
          />
        </section>

        <section className="section">
          <div className="section-title">
            <h2>System Architecture</h2>
            <p>End-to-end asynchronous inference pipeline</p>
          </div>

          <Architecture />
        </section>
      </main>
    </div>
  );
}