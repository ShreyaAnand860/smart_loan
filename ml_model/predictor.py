from decimal import Decimal

import joblib
import pandas as pd

from .train_model import FEATURES, MODEL_PATH, train_and_save


def _bundle():
    if not MODEL_PATH.exists():
        return train_and_save()
    return joblib.load(MODEL_PATH)


def _reason(payload, probability):
    reasons = []
    if payload["cibil_score"] < 650:
        reasons.append("CIBIL score is below the preferred threshold.")
    if payload["debt_to_income"] > 0.45:
        reasons.append("Existing obligations are high compared with annual income.")
    if payload["loan_amount"] > payload["salary"] * 60:
        reasons.append("Requested amount is high compared with verified salary.")
    if probability >= 0.5:
        return "Profile meets SmartLoan approval policy."
    return " ".join(reasons) or "Overall risk score is above SmartLoan policy tolerance."


def predict_loan(application):
    salary = float(Decimal(application.salary))
    existing = float(Decimal(application.existing_loans))
    payload = {
        "salary": salary,
        "existing_loans": existing,
        "cibil_score": int(application.cibil_score),
        "loan_amount": float(Decimal(application.loan_amount)),
        "loan_duration_months": int(application.loan_duration_months),
        "debt_to_income": existing / max(salary * 12, 1),
    }
    bundle = _bundle()
    df = pd.DataFrame([{k: payload[k] for k in FEATURES}])
    probability = float(bundle["model"].predict_proba(df)[0][1])
    risk_score = int(round((1 - probability) * 100))
    label = "Approved" if probability >= 0.5 else "Rejected"
    if risk_score < 35:
        risk_level = "Low"
    elif risk_score < 65:
        risk_level = "Medium"
    else:
        risk_level = "High"
    return {
        "label": label,
        "probability": round(probability * 100, 2),
        "risk_score": risk_score,
        "risk_level": risk_level,
        "reason": _reason(payload, probability),
        "model": bundle["model_name"],
        "model_accuracy": round(float(bundle["accuracy"]) * 100, 2),
    }
