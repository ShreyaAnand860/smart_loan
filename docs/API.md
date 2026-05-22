# SmartLoan API

Base path: `/api/`

Authentication uses JWT:

```http
POST /api/auth/token/
POST /api/auth/token/refresh/
```

Main resources:

- `/api/users/`
- `/api/loan-types/`
- `/api/loan-applications/`
- `/api/loan-applications/{id}/predict/`
- `/api/loan-applications/{id}/review/`
- `/api/documents/`
- `/api/emi-records/`
- `/api/payments/`
- `/api/credit-scores/`
- `/api/notifications/`
- `/api/dashboard/`
- `/api/emi-calculator/`

Officer review payload:

```json
{
  "decision": "APPROVED",
  "remarks": "Income and documents verified."
}
```

EMI calculator payload:

```json
{
  "principal": 1200000,
  "interest_rate": 10.5,
  "time": 60
}
```
