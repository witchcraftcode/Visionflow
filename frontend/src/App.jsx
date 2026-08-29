import { useState } from "react";
import { predict, getJob } from "./api";
import Navbar from "./components/Navbar";
import StatsGrid from "./components/StatsGrid";
import ModelSelector from "./components/ModelSelector";
import "./App.css";
import UploadCard from "./components/UploadCard";
import PredictionCard from "./components/PredictionCard";
import Architecture from "./components/Architecture";

export default function App() {
  const [file, setFile] = useState(null);
  const [selectedModel, setSelectedModel] = useState("resnet18");
  const [status, setStatus] = useState("Idle");
  const [result, setResult] = useState(null);
  const [jobId, setJobId] = useState(null);

  async function handlePredict() {
    if (!file) {
      alert("Please select an image first.");
      return;
    }

    setStatus("Uploading...");
    setResult(null);

    try {
      const job = await predict(file, selectedModel);

      setJobId(job.job_id);
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
    } catch (err) {
      console.error(err);
      setStatus("Error");
    }
  }

  return (
    <div className="app">
      <Navbar />

      <main className="container">
        <StatsGrid />

        <section className="hero">
          <h1>VisionFlow</h1>
          <p>Cloud-native ML Vision Inference Platform</p>
        </section>

        <ModelSelector
          selected={selectedModel}
          setSelected={setSelectedModel}
        />

        <UploadCard
          file={file}
          setFile={setFile}
          onPredict={handlePredict}
        />

        <section className="status-card">
          <h2>Inference Status</h2>

          <p>
            <strong>Status:</strong> {status}
          </p>

          <p>
            <strong>Model:</strong> {selectedModel}
          </p>

          {jobId && (
            <p>
              <strong>Job ID:</strong> {jobId}
            </p>
          )}
        </section>

        <PredictionCard
          result={result}
          model={selectedModel}
          status={status}
          jobId={jobId}
        />  

        <Architecture />
      </main>
    </div>
  );
}