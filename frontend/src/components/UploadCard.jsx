import { Upload, Image as ImageIcon, Play } from "lucide-react";

export default function UploadCard({
  file,
  setFile,
  selectedModel,
  onPredict,
  status,
}) {
  const preview = file ? URL.createObjectURL(file) : null;

  return (
    <div className="upload-card">
      <h2>Upload Image</h2>

      <label className="dropzone">
        {preview ? (
          <div className="file-preview">
            <img src={preview} alt="preview" />
          </div>
        ) : (
          <>
            <Upload size={42} />
            <h3>Drag & Drop Image</h3>
            <p>JPEG • PNG • WEBP</p>
            <span className="upload-btn">Choose File</span>
          </>
        )}

        <input
          type="file"
          accept="image/*"
          onChange={(e) => setFile(e.target.files[0])}
        />
      </label>

      {file && (
        <div className="file-info">
          <div className="file-name">
            <ImageIcon size={18} />
            <span>{file.name}</span>
          </div>

          <span>{(file.size / 1024).toFixed(1)} KB</span>
        </div>
      )}

      <div className="upload-meta">
        <div>
          <p>Selected Model</p>
          <h4>{selectedModel}</h4>
        </div>

        <div>
          <p>Status</p>
          <h4>{status}</h4>
        </div>
      </div>

      <button className="predict-btn" onClick={onPredict}>
        <Play size={18} />
        Run Inference
      </button>
    </div>
  );
}