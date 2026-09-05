"""
Hybrid ensemble anomaly detection:
  1. Isolation Forest        - fast, primary detector
  2. One-Class SVM           - tight-boundary complement
  3. Autoencoder (MLP-based) - reconstruction-error detector for
                                non-linear multi-parameter drift
  4. Mahalanobis distance    - classical statistical population check

Each detector's raw score is min-max normalised to [0, 1] and combined
via a weighted average into a single calibrated anomaly probability,
plus a confidence measure based on cross-detector agreement.
"""
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.covariance import EmpiricalCovariance

DEFAULT_WEIGHTS = {
    "isolation_forest": 0.35,
    "autoencoder": 0.30,
    "one_class_svm": 0.20,
    "mahalanobis": 0.15,
}


def _minmax(x):
    x = np.asarray(x, dtype=float)
    lo, hi = np.percentile(x, 1), np.percentile(x, 99)
    if hi - lo < 1e-9:
        return np.zeros_like(x)
    return np.clip((x - lo) / (hi - lo), 0, 1)


class HybridAnomalyEnsemble:
    """Fits four complementary anomaly detectors on the same feature
    matrix and exposes a single calibrated ensemble score per row.
    """

    def __init__(self, weights=None, random_state=42):
        self.weights = weights or DEFAULT_WEIGHTS
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.iforest = IsolationForest(
            n_estimators=200, contamination="auto", random_state=random_state
        )
        self.ocsvm = OneClassSVM(kernel="rbf", nu=0.1, gamma="scale")
        self.autoencoder = MLPRegressor(
            hidden_layer_sizes=(16, 4, 16), activation="tanh",
            max_iter=2000, random_state=random_state
        )
        self.cov_estimator = EmpiricalCovariance()
        self._fitted = False

    def fit(self, X):
        Xs = self.scaler.fit_transform(X)
        self.iforest.fit(Xs)
        self.ocsvm.fit(Xs)
        self.autoencoder.fit(Xs, Xs)  # trained to reconstruct its own input
        self.cov_estimator.fit(Xs)
        self._fitted = True
        return self

    def score(self, X):
        """Returns a DataFrame-ready dict of per-detector and ensemble scores."""
        if not self._fitted:
            raise RuntimeError("Call .fit(X) before .score(X).")
        Xs = self.scaler.transform(X)

        # 1. Isolation Forest: more negative = more anomalous -> flip sign
        if_raw = -self.iforest.score_samples(Xs)

        # 2. One-Class SVM: more negative decision_function = more anomalous
        ocsvm_raw = -self.ocsvm.decision_function(Xs)

        # 3. Autoencoder reconstruction error (MSE per row)
        recon = self.autoencoder.predict(Xs)
        ae_raw = np.mean((Xs - recon) ** 2, axis=1)

        # 4. Mahalanobis distance from the fitted (normal-dominant) population
        maha_raw = self.cov_estimator.mahalanobis(Xs)

        scores = {
            "anomaly_isolation_forest": _minmax(if_raw),
            "anomaly_autoencoder": _minmax(ae_raw),
            "anomaly_one_class_svm": _minmax(ocsvm_raw),
            "anomaly_mahalanobis": _minmax(maha_raw),
        }

        w = self.weights
        ensemble = (
            w["isolation_forest"] * scores["anomaly_isolation_forest"]
            + w["autoencoder"] * scores["anomaly_autoencoder"]
            + w["one_class_svm"] * scores["anomaly_one_class_svm"]
            + w["mahalanobis"] * scores["anomaly_mahalanobis"]
        )

        # cross-detector agreement (low std across detectors = high confidence)
        stacked = np.vstack([scores[k] for k in scores])
        agreement_std = stacked.std(axis=0)
        confidence = 1.0 - _minmax(agreement_std)  # high agreement -> high confidence

        scores["anomaly_ensemble_score"] = ensemble
        scores["anomaly_ensemble_confidence"] = confidence
        return scores
