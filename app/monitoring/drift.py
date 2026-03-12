import math
from collections import Counter, defaultdict


class DriftMonitor:
    def __init__(self, z_threshold: float = 3.0):
        self.z_threshold = z_threshold
        self._baseline_stats = {}
        self._current_sums = defaultdict(float)
        self._current_sumsq = defaultdict(float)
        self._current_counts = defaultdict(int)
        self._label_counter = Counter()

    def set_baseline(self, stats: dict):
        self._baseline_stats = stats

    def observe_features(self, features: dict):
        for key, value in features.items():
            if isinstance(value, (int, float)):
                v = float(value)
                self._current_sums[key] += v
                self._current_sumsq[key] += v * v
                self._current_counts[key] += 1

    def observe_prediction(self, label: str):
        self._label_counter[label] += 1

    def _current_mean_std(self, key: str):
        n = self._current_counts.get(key, 0)
        if n == 0:
            return None, None
        mean = self._current_sums[key] / n
        variance = max((self._current_sumsq[key] / n) - (mean * mean), 0.0)
        return mean, math.sqrt(variance)

    def feature_drift(self):
        findings = []
        for key, baseline in self._baseline_stats.items():
            baseline_mean = baseline.get("mean")
            baseline_std = baseline.get("std", 0.0)
            if baseline_mean is None or baseline_std <= 0:
                continue
            current_mean, _ = self._current_mean_std(key)
            if current_mean is None:
                continue
            z_score = abs(current_mean - baseline_mean) / baseline_std
            if z_score >= self.z_threshold:
                findings.append(
                    {
                        "feature": key,
                        "z_score": round(z_score, 4),
                        "baseline_mean": baseline_mean,
                        "current_mean": round(current_mean, 4),
                    }
                )
        return findings

    def prediction_distribution(self):
        total = sum(self._label_counter.values())
        if total == 0:
            return {}
        return {label: round(count / total, 4) for label, count in self._label_counter.items()}

    def summary(self):
        return {
            "feature_drift": self.feature_drift(),
            "prediction_distribution": self.prediction_distribution(),
            "samples": sum(self._current_counts.values()),
        }
