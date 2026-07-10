"""
Synthetic Data Generator
=========================
Generates realistic-looking fake events (dev edit sessions, service metrics)
so the whole system can be demoed WITHOUT needing real servers or a real
git repo connected. This guarantees the live demo never depends on external
uptime and lets the presenter trigger specific scenarios on demand.

Full scenario logic is implemented in Phase 9 of the build plan.
This file currently exposes the planned function signatures so the rest
of the app can import them without errors.
"""
import random

FAKE_FILES = ["auth.js", "checkout.py", "payment_service.py", "cart.js", "user_profile.py"]
FAKE_FUNCTIONS = ["validateLogin", "processPayment", "calculateTotal", "fetchUserData", "applyDiscount"]
FAKE_SERVICES = ["checkout-service", "auth-service", "payment-service", "search-service"]


def random_metrics_snapshot(force_anomaly: bool = False) -> dict:
    """Generate one fake metrics reading for a random (or forced-anomalous) service."""
    service = random.choice(FAKE_SERVICES)
    if force_anomaly:
        return {
            "service_name": service,
            "response_time_ms": random.randint(3000, 9000),
            "error_rate_pct": random.randint(40, 90),
            "db_pool_usage_pct": random.randint(85, 99),
            "affected_users_pct": random.randint(50, 95),
        }
    return {
        "service_name": service,
        "response_time_ms": random.randint(80, 400),
        "error_rate_pct": random.randint(0, 3),
        "db_pool_usage_pct": random.randint(20, 50),
        "affected_users_pct": random.randint(0, 5),
    }


def random_edit_event() -> dict:
    """Generate one fake 'developer started editing X' event."""
    return {
        "file_path": random.choice(FAKE_FILES),
        "function_name": random.choice(FAKE_FUNCTIONS),
    }
