"""
Federated Learning concept demo (Section 5.6 of the solution blueprint).

This is a standalone, self-contained illustration -- NOT wired into the
main pipeline -- showing how three simulated test labs can jointly
improve a shared anomaly-classification model via Federated Averaging
(FedAvg) WITHOUT centralising their raw telemetry: each lab trains a
local logistic-regression model on its own data, and only the model
COEFFICIENTS are averaged into a global model.

Run standalone:
    python src/federated_demo.py
"""
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split

from data_generator import generate_dataset
from features import build_dut_features, get_model_feature_columns


def _train_local_model(X, y, seed):
    clf = LogisticRegression(max_iter=1000, random_state=seed)
    clf.fit(X, y)
    return clf


def _fedavg(models, weights):
    """Weighted average of logistic-regression coefficients (FedAvg)."""
    coefs = np.average([m.coef_[0] for m in models], axis=0, weights=weights)
    intercepts = np.average([m.intercept_[0] for m in models], weights=weights)
    global_model = LogisticRegression()
    global_model.classes_ = models[0].classes_
    global_model.coef_ = coefs.reshape(1, -1)
    global_model.intercept_ = np.array([intercepts])
    return global_model


def run_demo():
    print("=" * 70)
    print("FEDERATED LEARNING DEMO -- BurnInGuard AI 2.0 (Section 5.6)")
    print("=" * 70)

    # Simulate 3 independent test labs by generating 3 separate datasets
    # with different random seeds / lot compositions (== different sites).
    lab_datasets = []
    for lab_idx, seed in enumerate([11, 22, 33]):
        raw = generate_dataset(n_lots=3, duts_per_lot=50, anomaly_fraction=0.10, seed=seed)
        feats = build_dut_features(raw)
        lab_datasets.append(feats)
        print(f"Lab {lab_idx + 1}: {len(feats)} DUTs "
              f"({feats['true_latent_defect'].sum()} labelled anomalies)")

    feature_cols = get_model_feature_columns(lab_datasets[0])

    local_models, local_test_sets, sizes = [], [], []
    for lab_idx, feats in enumerate(lab_datasets):
        X = feats[feature_cols].fillna(0).values
        y = feats["true_latent_defect"].values
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=lab_idx, stratify=y
        )
        model = _train_local_model(X_train, y_train, seed=lab_idx)
        local_models.append(model)
        local_test_sets.append((X_test, y_test))
        sizes.append(len(X_train))

        preds = model.predict(X_test)
        print(f"  Lab {lab_idx + 1} LOCAL-ONLY model  -> "
              f"acc={accuracy_score(y_test, preds):.2f}  f1={f1_score(y_test, preds, zero_division=0):.2f}")

    # Federated averaging: build one global model from local coefficients,
    # weighted by each lab's local training-set size.
    global_model = _fedavg(local_models, weights=sizes)

    print("\nEvaluating the FEDERATED GLOBAL model on each lab's own held-out test set:")
    for lab_idx, (X_test, y_test) in enumerate(local_test_sets):
        preds = global_model.predict(X_test)
        print(f"  Lab {lab_idx + 1} test set  -> "
              f"acc={accuracy_score(y_test, preds):.2f}  f1={f1_score(y_test, preds, zero_division=0):.2f}")

    print("\nNote: no lab's raw telemetry was ever shared -- only model")
    print("coefficients were exchanged and averaged (FedAvg).")


if __name__ == "__main__":
    run_demo()
