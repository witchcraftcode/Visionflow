import { CheckCircle, Cpu, Scan } from "lucide-react";

const models = [
  {
    id: "resnet18",
    name: "ResNet18",
    task: "Image Classification",
    icon: <CheckCircle size={28} />,
    badge: "Default",
  },
  {
    id: "mobilenet",
    name: "MobileNet",
    task: "Lightweight CNN",
    icon: <Cpu size={28} />,
    badge: "Fast",
  },
  {
    id: "yolov5",
    name: "YOLOv5",
    task: "Object Detection",
    icon: <Scan size={28} />,
    badge: "Detection",
  },
];

export default function ModelSelector({ selected, setSelected }) {
  return (
    <div className="models">
      {models.map((model) => (
        <button
          key={model.id}
          className={`model-card ${
            selected === model.id ? "active" : ""
          }`}
          onClick={() => setSelected(model.id)}
        >
          <div className="model-icon">{model.icon}</div>

          <div className="model-badge">{model.badge}</div>

          <h3>{model.name}</h3>

          <p>{model.task}</p>

          {selected === model.id && (
            <div className="selected-text">Selected</div>
          )}
        </button>
      ))}
    </div>
  );
}