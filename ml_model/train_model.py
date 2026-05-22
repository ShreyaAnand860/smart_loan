from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "sample_loan_dataset.csv"
MODEL_PATH = BASE_DIR / "loan_model.joblib"

FEATURES = [
    "salary",
    "existing_loans",
    "cibil_score",
    "loan_amount",
    "loan_duration_months",
    "debt_to_income",
]


def generate_dataset(rows=1200, seed=42):
    rng = np.random.default_rng(seed)
    salary = rng.integers(18000, 350000, rows)
    existing_loans = rng.integers(0, 2500000, rows)
    cibil_score = rng.integers(300, 901, rows)
    loan_amount = rng.integers(50000, 10000000, rows)
    duration = rng.integers(6, 361, rows)
    debt_to_income = existing_loans / np.maximum(salary * 12, 1)
    affordability = salary * 48 - loan_amount * 0.18 - existing_loans * 0.35
    score = (
        (cibil_score - 300) / 600
        + np.clip(affordability / 6000000, -1, 1)
        - np.clip(debt_to_income, 0, 2) * 0.55
        - (duration > 180) * 0.1
    )
    approved = (score + rng.normal(0, 0.12, rows) > 0.42).astype(int)
    df = pd.DataFrame(
        {
            "salary": salary,
            "existing_loans": existing_loans,
            "cibil_score": cibil_score,
            "loan_amount": loan_amount,
            "loan_duration_months": duration,
            "debt_to_income": debt_to_income.round(4),
            "approved": approved,
        }
    )
    DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(DATASET_PATH, index=False)
    return df


def train_and_save():
    df = pd.read_csv(DATASET_PATH) if DATASET_PATH.exists() else generate_dataset()
    x = df[FEATURES]
    y = df["approved"]
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.22, random_state=7, stratify=y)
    logistic = Pipeline([("scale", StandardScaler()), ("model", LogisticRegression(max_iter=1000))])
    forest = RandomForestClassifier(n_estimators=180, max_depth=9, min_samples_leaf=4, random_state=7)
    logistic.fit(x_train, y_train)
    forest.fit(x_train, y_train)
    candidates = {"logistic_regression": logistic, "random_forest": forest}
    scored = {name: accuracy_score(y_test, model.predict(x_test)) for name, model in candidates.items()}
    best_name = max(scored, key=scored.get)
    bundle = {"model": candidates[best_name], "model_name": best_name, "accuracy": scored[best_name], "features": FEATURES}
    joblib.dump(bundle, MODEL_PATH)
    return bundle


if __name__ == "__main__":
    bundle = train_and_save()
    print(f"Saved {bundle['model_name']} with accuracy {bundle['accuracy']:.3f}")
