from app.monitoring import DriftMonitor


def main():
    monitor = DriftMonitor()
    monitor.set_baseline({"feature_1": {"mean": 0.0, "std": 1.0}})
    monitor.observe_features({"feature_1": 0.1})
    monitor.observe_prediction("class_a")
    print(monitor.summary())


if __name__ == "__main__":
    main()
