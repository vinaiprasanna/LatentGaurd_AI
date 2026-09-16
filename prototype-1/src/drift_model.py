"""
Drift / remaining-margin prediction.

Primary model: XGBoost regressor trained on EARLY checkpoint features
(0h + physics-informed drift proxies + lot statistics) to predict the
168h (end-of-burn-in) value of each monitored parameter.

Two additional quantile-objective XGBoost models (10th / 90th
percentile) provide a prediction interval.

If xgboost is not installed in the environment, this module
automatically falls back to sklearn's GradientBoostingRegressor with
quantile loss, so the PoC still runs end-to-end.
"""
import numpy as np

try:
    import xgboost as xgb
    _HAS_XGB = True
except ImportError:
    _HAS_XGB = False
    from sklearn.ensemble import GradientBoostingRegressor


class DriftPredictor:
    """One instance predicts the end-of-burn-in value (and interval) for
    a single monitored parameter (e.g. iddq_uA)."""

    def __init__(self, param_name, random_state=42):
        self.param_name = param_name
        self.random_state = random_state
        self._build_models()
        self._fitted = False

    def _build_models(self):
        if _HAS_XGB:
            common = dict(n_estimators=150, max_depth=3, learning_rate=0.08,
                          random_state=self.random_state)
            self.model_mean = xgb.XGBRegressor(objective="reg:squarederror", **common)
            self.model_lo = xgb.XGBRegressor(objective="reg:quantileerror",
                                                  quantile_alpha=0.10, **common)
            self.model_hi = xgb.XGBRegressor(objective="reg:quantileerror",
                                                  quantile_alpha=0.90, **common)
        else:
            common = dict(n_estimators=150, max_depth=3, learning_rate=0.08,
                          random_state=self.random_state)
            self.model_mean = GradientBoostingRegressor(loss="squared_error", **common)
            self.model_lo = GradientBoostingRegressor(loss="quantile", alpha=0.10, **common)
            self.model_hi = GradientBoostingRegressor(loss="quantile", alpha=0.90, **common)

    def fit(self, X, y):
        self.model_mean.fit(X, y)
        self.model_lo.fit(X, y)
        self.model_hi.fit(X, y)
        self._fitted = True
        return self

    def predict(self, X):
        if not self._fitted:
            raise RuntimeError("Call .fit(X, y) before .predict(X).")
        mean = self.model_mean.predict(X)
        lo = self.model_lo.predict(X)
        hi = self.model_hi.predict(X)
        lo, hi = np.minimum(lo, hi), np.maximum(lo, hi)
        mean = np.clip(mean, lo, hi)
        interval_width = hi - lo
        return {
            f"{self.param_name}_pred_168h": mean,
            f"{self.param_name}_pred_168h_lo": lo,
            f"{self.param_name}_pred_168h_hi": hi,
            f"{self.param_name}_pred_interval_width": interval_width,
        }

    def feature_importances(self, feature_names):
        try:
            importances = self.model_mean.feature_importances_
            return dict(sorted(zip(feature_names, importances),
                                key=lambda kv: -kv[1]))
        except AttributeError:
            return {}
