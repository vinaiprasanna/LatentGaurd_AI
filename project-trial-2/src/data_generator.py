"""
BurnInGuard AI 2.0 - Synthetic Burn-In Data Generator
------------------------------------------------------
Generates realistic-looking (but synthetic) burn-in telemetry for a
population of DUTs (Devices Under Test) across multiple manufacturing
lots, at measurement checkpoints 0h / 24h / 96h / 168h.

A small fraction of DUTs are seeded with "latent defect" behaviour:
their electrical parameters remain within the static PASS/FAIL limit
but drift abnormally fast relative to their lot -- this is exactly the
class of component that static-limit screening misses and that
BurnInGuard AI is designed to catch.

NOTE: This is synthetic data for demonstration purposes only and must
never be presented as real ISRO / DRDO / manufacturer test data.
"""
import numpy as np
import pandas as pd

CHECKPOINTS_H = [0, 24, 96, 168]
STATIC_LIMITS = {
    "iddq_uA": 50.0,      # standby current limit
    "leakage_uA": 10.0,   # leakage current limit
    "delay_ns": 8.0,      # propagation delay limit
}


def _arrhenius_factor(temp_c, ea_ev=0.7, temp_ref_c=125.0, k_boltzmann=8.617e-5):
    """Simple Arrhenius acceleration factor relative to a reference temperature.
    Higher temperature -> faster expected degradation (used to scale drift).
    """
    t_kelvin = temp_c + 273.15
    t_ref_kelvin = temp_ref_c + 273.15
    return np.exp((ea_ev / k_boltzmann) * (1.0 / t_ref_kelvin - 1.0 / t_kelvin))


def generate_dataset(
    n_lots=6,
    duts_per_lot=40,
    anomaly_fraction=0.08,
    seed=42,
):
    """Generate a synthetic burn-in telemetry dataset.

    Returns
    -------
    pandas.DataFrame with one row per (DUT, checkpoint).
    """
    rng = np.random.default_rng(seed)
    rows = []
    dut_counter = 1

    for lot_idx in range(n_lots):
        lot_id = f"LOT{2026}{chr(65 + lot_idx)}"
        lot_base_iddq = rng.normal(10.0, 1.0)
        lot_base_leak = rng.normal(2.0, 0.2)
        lot_base_delay = rng.normal(5.0, 0.15)
        lot_temp = rng.choice([110.0, 125.0, 135.0])

        n_anomalous = max(1, int(round(duts_per_lot * anomaly_fraction)))
        anomaly_flags = np.array([1] * n_anomalous + [0] * (duts_per_lot - n_anomalous))
        rng.shuffle(anomaly_flags)

        for i in range(duts_per_lot):
            dut_id = f"IC{dut_counter:04d}"
            dut_counter += 1
            is_anomalous = bool(anomaly_flags[i])
            dut_temp = lot_temp + rng.normal(0, 1.5)
            accel = _arrhenius_factor(dut_temp)

            iddq0 = max(0.5, lot_base_iddq + rng.normal(0, 0.6))
            leak0 = max(0.2, lot_base_leak + rng.normal(0, 0.1))
            delay0 = max(1.0, lot_base_delay + rng.normal(0, 0.08))

            if is_anomalous:
                drift_mult = rng.uniform(3.5, 7.0)
                curvature = rng.uniform(1.4, 2.2)
            else:
                drift_mult = rng.uniform(0.8, 1.6)
                curvature = rng.uniform(0.9, 1.15)

            for t in CHECKPOINTS_H:
                frac = (t / max(CHECKPOINTS_H)) ** curvature
                noise = rng.normal(0, 0.03)

                iddq = iddq0 * (1 + drift_mult * accel * 0.28 * frac) + rng.normal(0, 0.15)
                leak = leak0 * (1 + drift_mult * accel * 0.22 * frac) + rng.normal(0, 0.03)
                delay = delay0 * (1 + drift_mult * accel * 0.05 * frac) + rng.normal(0, 0.02)

                iddq = max(0.1, iddq + noise)
                leak = max(0.05, leak + noise * 0.2)
                delay = max(0.5, delay + noise * 0.1)

                status = "PASS"
                if (iddq > STATIC_LIMITS["iddq_uA"] or leak > STATIC_LIMITS["leakage_uA"]
                        or delay > STATIC_LIMITS["delay_ns"]):
                    status = "FAIL"

                rows.append({
                    "dut_id": dut_id,
                    "lot_id": lot_id,
                    "checkpoint_h": t,
                    "temperature_c": round(dut_temp, 2),
                    "vcc_v": round(rng.normal(5.0, 0.02), 3),
                    "iddq_uA": round(iddq, 3),
                    "leakage_uA": round(leak, 3),
                    "delay_ns": round(delay, 3),
                    "status": status,
                    "true_latent_defect": int(is_anomalous),
                })

    df = pd.DataFrame(rows)
    return df


if __name__ == "__main__":
    df = generate_dataset()
    out_path = "/media/steffan/new/Projects/LatentGaurd_AI/project-trial-2/data/synthetic_burnin_data.csv"
    df.to_csv(out_path, index=False)
    print(f"Generated {df['dut_id'].nunique()} DUTs, {len(df)} rows -> {out_path}")
    print(df.groupby("checkpoint_h")["status"].value_counts())
