"""
PCA-SPC (Principal Component Analysis + Statistical Process Control)
Anomaly Detector.

Uses PCA to reduce feature dimensionality, then applies SPC control
chart statistics (Hotelling's T-squared and Q / squared prediction
error) to detect anomalous DUTs.

The T-squared statistic measures how far a sample is from the model
center in the principal component space.
The Q statistic measures the residual variance not captured by the
selected principal components.
Both are compared against chi-square-based control limits.
"""
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from scipy.stats import chi2


class PCASPCDetector:
    """Fits PCA on the feature matrix and uses Hotelling's T-squared
    and Q statistics as anomaly scores.
    """

    def __init__(self, n_components=None, variance_retained=0.95, random_state=42):
        self.n_components = n_components
        self.variance_retained = variance_retained
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.pca = None
        self.n_selected_ = 0
        self.t2_limit_ = 0.0
        self.q_limit_ = 0.0
        self._fitted = False

    def fit(self, X):
        Xs = self.scaler.fit_transform(X)
        n_samples, n_features = Xs.shape

        if self.n_components is not None:
            k = min(self.n_components, n_features)
        else:
            self.pca = PCA(n_components=self.variance_retained, random_state=self.random_state)
            self.pca.fit(Xs)
            k = self.pca.n_components_

        self.n_selected_ = k
        self.pca = PCA(n_components=k, random_state=self.random_state)
        self.pca.fit(Xs)

        # Transform data to principal component space
        Z = self.pca.transform(Xs)

        # Compute T-squared control limit using F-distribution
        # T^2 = sum(z_i^2 / lambda_i) where lambda_i are eigenvalues
        eigenvalues = self.pca.explained_variance_
        # Use the simplified Hotelling's T^2 limit
        alpha = 0.01  # 99% control limit
        p = k
        n = n_samples
        t2_limit = p * (n - 1) * (n + 1) / (n * (n - p)) * chi2.ppf(1 - alpha, p) / n

        # Compute Q (SPE) control limit using chi-square approximation
        # Using Jackson's approximation
        q_eigenvalues = np.sum(self.pca.explained_variance_[k:]) if k < n_features else 0.0
        if q_eigenvalues > 0:
            # Approximate Q limit using chi-square
            q_limit = np.sum(self.pca.explained_variance_[k:]) ** 2 / np.sum(self.pca.explained_variance_[k:] ** 2) * chi2.ppf(1 - alpha, 1)
        else:
            q_limit = 0.0

        self.t2_limit_ = t2_limit
        self.q_limit_ = q_limit
        self._fitted = True
        return self

    def score(self, X):
        """Returns T-squared and Q-based anomaly scores in [0, 1]."""
        if not self._fitted:
            raise RuntimeError("Call .fit(X) before .score(X).")

        Xs = self.scaler.transform(X)
        Z = self.pca.transform(Xs)
        eigenvalues = self.pca.explained_variance_

        # T-squared: sum of squared scores weighted by eigenvalues
        t2_scores = np.sum(Z ** 2 / eigenvalues, axis=1)

        # Q statistic: squared prediction error (residual after PCA)
        X_reconstructed = self.pca.inverse_transform(Z)
        q_scores = np.sum((Xs - X_reconstructed) ** 2, axis=1)

        # Normalize to [0, 1] using min-max with control limit as reference
        t2_score = _minmax_t2(t2_scores, self.t2_limit_)
        q_score = _minmax_q(q_scores, self.q_limit_)

        # Combined score: average of T2 and Q normalized scores
        ensemble = 0.5 * t2_score + 0.5 * q_score

        return {
            "anomaly_pca_spc_t2": t2_score,
            "anomaly_pca_spc_q": q_score,
            "anomaly_pca_spc": ensemble,
        }

    def feature_importances(self, feature_names):
        """Return the absolute loading sum of each feature across
        selected principal components as a rough importance measure."""
        if self.pca is None or not self._fitted:
            return {}
        loadings = np.abs(self.pca.components_)
        importance = loadings.sum(axis=0)
        return dict(sorted(zip(feature_names, importance), key=lambda kv: -kv[1]))


def _minmax_t2(t2_scores, t2_limit):
    """Normalize T-squared scores: values near 0 are normal, values
    approaching or exceeding t2_limit are anomalous."""
    t2_scores = np.asarray(t2_scores, dtype=float)
    # Clip at limit for scaling
    clipped = np.clip(t2_scores / max(t2_limit, 1e-9), 0, 1)
    return clipped


def _minmax_q(q_scores, q_limit):
    """Normalize Q scores similarly."""
    q_scores = np.asarray(q_scores, dtype=float)
    clipped = np.clip(q_scores / max(q_limit, 1e-9), 0, 1)
    return clipped
