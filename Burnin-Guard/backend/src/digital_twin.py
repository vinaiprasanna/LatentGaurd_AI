"""
Digital Twin (simplified PoC version).

Given a DUT's early-checkpoint physics-normalised drift rate and its
Arrhenius acceleration factor, project its parameter trajectory beyond
the end of burn-in (168h) so a QA engineer can "fast-forward" a
component's projected behaviour and see its remaining margin against
the static safety limit at, e.g., 500h.
"""
import numpy as np


def project_trajectory(v0, physics_norm_slope, accel_factor, horizons_h=(168, 300, 500, 1000)):
    """Simple physics-consistent extrapolation:
       v(t) = v0 + (physics_norm_slope * accel_factor) * t
       i.e. re-apply the Arrhenius acceleration to the physics-normalised
       (temperature-independent) drift rate to project forward in time.
    """
    slope = physics_norm_slope * accel_factor
    return {int(h): float(v0 + slope * h) for h in horizons_h}


def remaining_margin(projection: dict, static_limit: float, horizon_h: int):
    """Returns remaining margin (can be negative if already over limit)
    at a given horizon, as an absolute value and as a percentage of the
    limit."""
    v = projection.get(int(horizon_h))
    if v is None:
        return None
    margin_abs = static_limit - v
    margin_pct = (margin_abs / static_limit) * 100.0
    return {"projected_value": v, "margin_abs": margin_abs, "margin_pct": margin_pct}
