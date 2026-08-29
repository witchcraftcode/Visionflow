import { FileImage, Loader2, Play, UploadCloud } from "lucide-react";
import { useRef, useState } from "react";

const ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/webp"];
const MAX_BYTES = 10 * 1024 * 1024;

function formatBytes(bytes) {
  if (!bytes) return "0 KB";
  if (bytes >= 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
  return `${(bytes / 1024).toFixed(1)} KB`;
}

export default function UploadPanel({
  file,
  isProcessing,
  onFileSelect,
  onRunInference,
  selectedModel,
  status,
}) {
  const inputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const [validationError, setValidationError] = useState("");

  const pickFile = (nextFile) => {
    if (!nextFile) return;

    if (!ACCEPTED_TYPES.includes(nextFile.type)) {
      setValidationError("Use a JPG, PNG, or WEBP image.");
      return;
    }

    if (nextFile.size > MAX_BYTES) {
      setValidationError("Image must be 10MB or smaller.");
      return;
    }

    setValidationError("");
    onFileSelect(nextFile);
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setIsDragging(false);
    pickFile(event.dataTransfer.files?.[0]);
  };

  return (
    <section className="tool-panel upload-panel">
      <div className="panel-heading">
        <p>Upload Panel</p>
        <h2>Run a queued vision inference</h2>
      </div>

      <div
        className={`dropzone ${isDragging ? "is-dragging" : ""}`}
        onDragEnter={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={(event) => {
          event.preventDefault();
          setIsDragging(false);
        }}
        onDragOver={(event) => event.preventDefault()}
        onDrop={handleDrop}
      >
        <UploadCloud size={34} />
        <h3>Drag and drop image</h3>
        <p>JPG, PNG, WEBP. Max 10MB.</p>
        <button className="browse-button" onClick={() => inputRef.current?.click()} type="button">
          Browse files
        </button>
        <input
          accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp"
          onChange={(event) => pickFile(event.target.files?.[0])}
          ref={inputRef}
          type="file"
        />
      </div>

      {validationError && <p className="validation-error">{validationError}</p>}

      {file && (
        <div className="selected-file">
          <FileImage size={18} />
          <div>
            <strong>{file.name}</strong>
            <span>{formatBytes(file.size)}</span>
          </div>
        </div>
      )}

      <div className="run-summary">
        <div>
          <span>Selected model</span>
          <strong>{selectedModel.name}</strong>
        </div>
        <div>
          <span>Pipeline status</span>
          <strong>{status || "idle"}</strong>
        </div>
      </div>

      <button
        className="run-button"
        disabled={!file || isProcessing}
        onClick={onRunInference}
        type="button"
      >
        {isProcessing ? <Loader2 className="spin" size={18} /> : <Play size={18} />}
        {isProcessing ? "Processing" : "Run Inference"}
      </button>
    </section>
  );
}
