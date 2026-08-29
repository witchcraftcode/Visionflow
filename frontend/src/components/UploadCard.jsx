import { useRef } from "react";
import { Upload, Image } from "lucide-react";

export default function UploadCard({ file, setFile, onPredict }) {
  const inputRef = useRef();

  function handleDrop(e) {
    e.preventDefault();
    const dropped = e.dataTransfer.files[0];
    if (dropped) setFile(dropped);
  }

  return (
    <section className="upload-card">
      <h2>Image Upload</h2>

      <div
        className="dropzone"
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        onClick={() => inputRef.current.click()}
      >
        {file ? (
          <>
            <img
              src={URL.createObjectURL(file)}
              alt="preview"
              className="preview"
            />
            <p>{file.name}</p>
          </>
        ) : (
          <>
            <Upload size={40} />
            <h3>Drag & Drop</h3>
            <p>JPEG • PNG • WEBP</p>
          </>
        )}

        <input
          ref={inputRef}
          hidden
          type="file"
          accept="image/*"
          onChange={(e) => setFile(e.target.files[0])}
        />
      </div>

      <button className="predict-btn" onClick={onPredict}>
        <Image size={18} />
        Run Inference
      </button>
    </section>
  );
}