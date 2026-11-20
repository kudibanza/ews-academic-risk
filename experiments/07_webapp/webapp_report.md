# Web Prototype Report — Sub-step 7.3 (RQ5)

Minimal proof-of-concept prototype serving the §14 SHAP artifacts.
Built as a validation vehicle for the SCS evaluation, not a production
system.

## 1. Architecture

- **Backend:** FastAPI, SQLAlchemy 2.0 (async), PostgreSQL 15+, Pydantic v2.
  Authentication via JWT (HS256) with `pwdlib` (argon2).
- **Frontend:** React 19, Vite, TypeScript, Tailwind CSS v4, TanStack Query v5,
  React Router v7, Recharts.
- **Database schema:** `users` (id, username, hashed_password, role, active)
  and `artifacts_cache` (id, student_id, presentation, window, risk_score,
  threshold_applied, flagged, top_positive_factors, top_negative_factors,
  other_factors_sum, base_value).

## 2. Data and Serving

The prototype does not recompute SHAP values in real time. It caches a
stratified sample of the out-of-fold artifacts generated in Step 5.
- Seeded: 500 students per window (W2, W4, W6, W8), 50% flagged / 50% not.
- Serving is a simple DB read by `student_id` and `window`. Latency
  measured locally is < 20 ms per request, well within the < 200 ms target
  at 10 concurrent sessions.

## 3. User Roles and Interface

Two roles are implemented:
- **Advisor:** Can view the at-risk student list (sorted by risk score
  descending, with pagination and student ID search), view individual risk
  cards (with SHAP explanations), and submit the SCS survey.
- **Admin:** Can do everything an advisor can, plus access the Admin
  Dashboard (aggregated stats, priority intervention table, risk evolution
  chart) and User Management (create users, change roles, deactivate, change
  passwords).

The UI translates the technical SHAP outputs into an actionable interface:
risk scores are shown as percentages, contributions are color-coded
(red for risk, green for protection), and the base_value/other_factors_sum
are hidden from the user.

## 4. Limitations

- **Seeded sample:** The prototype uses a 2,000-student sample, not the
  full 109k artifacts. This is intentional for demo performance; the backend
  handles the full dataset if `N_PER_WINDOW` is increased in `seed.py`.
- **No real-time inference:** The system serves pre-computed artifacts. In
  a production deployment, the backend would query the ML pipeline.
- **Authentication:** Local JWT only. Out of scope: SSO, OAuth2, password reset.

## 5. Reproducibility

- Backend: `uvicorn app.main:app --reload` (port 8000).
- Frontend: `npm run dev` (port 3000).
- Seed: `python -m app.seed`.
- Endpoints tested via the auto-generated Swagger UI (`/docs`).