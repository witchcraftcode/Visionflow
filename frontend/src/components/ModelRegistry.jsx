import { Boxes, Check, Cpu, ScanSearch, Zap } from "lucide-react";

const iconsByModel = {
  resnet18: Boxes,
  mobilenet: Zap,
  yolov5: ScanSearch,
};

export default function ModelRegistry({ models, selectedModel, onSelectModel }) {
  return (
    <div className="model-grid" role="radiogroup" aria-label="Model registry">
      {models.map((model) => {
        const Icon = iconsByModel[model.id] || Cpu;
        const isSelected = selectedModel === model.id;

        return (
          <button
            aria-checked={isSelected}
            className={`model-card accent-${model.accent} ${isSelected ? "is-selected" : ""}`}
            key={model.id}
            onClick={() => onSelectModel(model.id)}
            role="radio"
            type="button"
          >
            <div className="model-card-header">
              <span className="model-icon">
                <Icon size={20} />
              </span>
              <span className="model-badge">{model.badge}</span>
            </div>
            <h3>{model.name}</h3>
            <p className="model-task">{model.task}</p>
            <p>{model.description}</p>
            <span className="selection-indicator">
              <Check size={15} />
              Selected
            </span>
          </button>
        );
      })}
    </div>
  );
}
