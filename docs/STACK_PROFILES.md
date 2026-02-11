# Stack Profiles

## web_vite_react_ts
- scaffold: npm create vite@latest web -- --template react-ts
- run: cd web && npm i && npm run dev
- test: cd web && npm test (if configured)

## api_fastapi_py
- scaffold: mkdir api && python3 -m venv .venv
- run: uvicorn app:app --reload
- test: pytest (if present)
