const models = [
  {
    id: "resnet18",
    name: "ResNet18",
    task: "Classification",
  },
  {
    id: "mobilenet",
    name: "MobileNet",
    task: "Lightweight CNN",
  },
  {
    id: "yolov5",
    name: "YOLOv5",
    task: "Object Detection",
  },
];

export default function ModelSelector({ selected, setSelected }) {
  return (
    <div className="models">
      {models.map((m) => (
        <button
          key={m.id}
          className={selected === m.id ? "active" : ""}
          onClick={() => setSelected(m.id)}
        >
          <h3>{m.name}</h3>
          <p>{m.task}</p>
        </button>
      ))}
    </div>
  );
}