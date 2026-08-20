from fastapi import APIRouter

from app.monitoring import DriftMonitor
from app.schemas.monitoring import DriftBaselineRequest, DriftObserveRequest

router = APIRouter()
DRIFT_MONITOR = DriftMonitor()


@router.post("/monitoring/drift/baseline")
def set_drift_baseline(request: DriftBaselineRequest):
    DRIFT_MONITOR.set_baseline(request.baseline)
    return {"status": "baseline_set", "features": sorted(request.baseline.keys())}


@router.post("/monitoring/drift/observe")
def observe_drift(request: DriftObserveRequest):
    DRIFT_MONITOR.observe_features(request.features)
    if request.label is not None:
        DRIFT_MONITOR.observe_prediction(request.label)
    return {"status": "observed"}


@router.get("/monitoring/drift/summary")
def drift_summary():
    return DRIFT_MONITOR.summary()
