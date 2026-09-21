"""
Hybrid ensemble anomaly detection:
  1. XGBoost Classifier   - supervised gradient-boosting detector
  2. Random Forest        - ensemble tree-based detector
  3. PCA-SPC              - PCA + Statistical Process Control
     (Hotelling's T-squared and Q statistics)

Each detector's raw score is min-max normalised to [0, 1] and
combined via a weighted average into a single calibrated anomaly
probability, plus a confidence measure based on cross-detector
agreement.
"""
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report

try:
    from xgboost import XGBClassifier
    _HAS_XGB = True
except ImportError:
    _HAS_XGB = False

from spc import PCASPCDetector

DEFAULT_WEIGHTS = {
    "xgboost": 0.35,
    "random_forest": 0.35,
    "pca_spc": 0.30,
}


def _minmax(x):
    x = np.asarray(x, dtype=float)
    lo, hi = np.percentile(x, 1), np.percentile(x, 99)
    if hi - lo < 1e-9:
        return np.zeros_like(x)
    return np.clip((x - lo) / (hi - lo), 0, 1)


def _calibration_bounds(x):
    x = np.asarray(x, dtype=float)
    return float(np.percentile(x, 1)), float(np.percentile(x, 99))


def _scale_with_bounds(x, bounds):
    x = np.asarray(x, dtype=float)
    lo, hi = bounds
    if hi - lo < 1e-9:
        return np.zeros_like(x)
    return np.clip((x - lo) / (hi - lo), 0, 1)


class HybridAnomalyEnsemble:
    """Fits XGBoost, Random Forest, and PCA-SPC detectors on the
    same feature matrix and exposes a single calibrated ensemble
    score per row.
    """

    def __init__(self, weights=None, random_state=42):
        self.weights = weights or DEFAULT_WEIGHTS
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.pca_spc = PCASPCDetector(variance_retained=0.95, random_state=random_state)
        if _HAS_XGB:
            self.xgb_model = XGBClassifier(
                n_estimators=200, max_depth=4, learning_rate=0.08,
                random_state=random_state
            )
        else:
            self.xgb_model = None
        self.rf_model = RandomForestClassifier(
            n_estimators=200, max_depth=6, random_state=random_state
        )
        self.calibration_bounds = None
        self._fitted = False

    def fit(self, X, y):
        """Fit all detectors on feature matrix X with labels y.

        XGBoost and Random Forest are trained as supervised
        classifiers. PCA-SPC is trained unsupervised.
        """
        Xs = self.scaler.fit_transform(X)

        # Fit PCA-SPC (unsupervised)
        self.pca_spc.fit(X)

        # Fit XGBoost and Random Forest (supervised)
        self.xgb_model.fit(Xs, y)
        self.rf_model.fit(Xs, y)

        raw_scores = self._raw_scores(X, Xs)
        self.calibration_bounds = {
            name: _calibration_bounds(values)
            for name, values in raw_scores.items()
        }

        self._fitted = True
        return self

    def _raw_scores(self, X, Xs):
        spc_scores = self.pca_spc.score(X)
        n_samples = X.shape[0]
        if _HAS_XGB and self.xgb_model is not None:
            xgb_raw = self.xgb_model.predict_proba(Xs)[:, 1]
        else:
            xgb_raw = np.zeros(n_samples)
        return {
            "anomaly_xgboost": xgb_raw,
            "anomaly_random_forest": self.rf_model.predict_proba(Xs)[:, 1],
            "anomaly_pca_spc": spc_scores["anomaly_pca_spc"],
        }

    def score(self, X, y=None):
        """Returns a dict of per-detector and ensemble scores.

        If y is provided, supervised probabilities are used for
        XGBoost and Random Forest. Otherwise, anomaly scores are
        derived from PCA-SPC and model-based outlierness.
        """
        if not self._fitted:
            raise RuntimeError("Call .fit(X) before .score(X).")

        Xs = self.scaler.transform(X)
        n_samples = X.shape[0]

        raw_scores = self._raw_scores(X, Xs)
        bounds = self.calibration_bounds
        if bounds is None:
            bounds = {name: _calibration_bounds(values) for name, values in raw_scores.items()}

        scores = {
            name: _scale_with_bounds(values, bounds[name])
            for name, values in raw_scores.items()
        }

        w = self.weights
        ensemble = (
            w["xgboost"] * scores["anomaly_xgboost"]
            + w["random_forest"] * scores["anomaly_random_forest"]
            + w["pca_spc"] * scores["anomaly_pca_spc"]
        )

        # Cross-detector agreement
        stacked = np.vstack([scores[k] for k in scores])
        agreement_std = stacked.std(axis=0)
        confidence = 1.0 - _minmax(agreement_std)

        scores["anomaly_ensemble_score"] = ensemble
        scores["anomaly_ensemble_confidence"] = confidence
        return scores


def evaluate_ensemble(dut_df, y_true, risk_threshold=60):
    """Compute classification metrics comparing HIGH/CRITICAL
    flags against ground-truth latent defect labels."""
    from sklearn.metrics import classification_report
    y_pred = (dut_df["risk_score"] >= risk_threshold).astype(int).values
    report = classification_report(
        y_true, y_pred,
        target_names=["normal", "latent_defect"],
        zero_division=0,
        output_dict=False,
    )
    return report, y_pred
