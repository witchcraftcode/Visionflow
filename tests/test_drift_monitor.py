from app.monitoring import DriftMonitor


def test_drift_monitor_detects_feature_drift():
    monitor = DriftMonitor(z_threshold=2.0)
    monitor.set_baseline({"f1": {"mean": 0.0, "std": 1.0}})
    monitor.observe_features({"f1": 3.0})
    summary = monitor.summary()
    assert len(summary["feature_drift"]) == 1
    assert summary["feature_drift"][0]["feature"] == "f1"


def test_drift_monitor_prediction_distribution():
    monitor = DriftMonitor()
    monitor.observe_prediction("cat")
    monitor.observe_prediction("cat")
    monitor.observe_prediction("dog")
    dist = monitor.prediction_distribution()
    assert dist["cat"] == 0.6667
    assert dist["dog"] == 0.3333
