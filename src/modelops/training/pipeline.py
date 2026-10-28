"""sklearn Pipeline construction for the Milestone 1 baseline."""

from __future__ import annotations

from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from modelops.data.features import FEATURE_COLUMNS

NUMERIC_FEATURES = ("passenger_count", "pickup_hour", "pickup_dow", "pickup_day")
CATEGORICAL_FEATURES = ("PULocationID", "DOLocationID")


def build_baseline_pipeline(*, random_seed: int = 42) -> Pipeline:
    """Preprocess + linear (Ridge) baseline.

    Location IDs are one-hot encoded (unknown categories ignored at predict time).
    Numeric time/passenger fields are standardized.

    Ridge is used instead of ordinary least squares because one-hot taxi zones
    create a wide, collinear design matrix; unregularized LinearRegression is
    numerically unstable on that encoding. This remains a linear baseline.
    ``random_seed`` is reserved for later stochastic models.
    """
    del random_seed  # reserved for RandomForest and similar later

    # Guard against accidental feature drift between modules.
    expected = set(FEATURE_COLUMNS)
    actual = set(NUMERIC_FEATURES) | set(CATEGORICAL_FEATURES)
    if expected != actual:
        raise RuntimeError(f"Feature mismatch: expected {expected}, pipeline has {actual}")

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), list(NUMERIC_FEATURES)),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=True),
                list(CATEGORICAL_FEATURES),
            ),
        ],
        remainder="drop",
        sparse_threshold=0.3,
    )
    return Pipeline(
        steps=[
            ("preprocess", preprocessor),
            ("model", Ridge(alpha=1.0)),
        ]
    )
