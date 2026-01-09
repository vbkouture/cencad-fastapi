$env:PATH = "$PWD\.venv\Scripts;$env:PATH"; git commit -m "reproduce issue"

<!-- Testing coverage check -->

run pytest --collect-only -q to see the list at any time, or generate a coverage report with pytest --cov

<!-- Pre-commit hooks fixed - now uses .venv Python automatically -->

<!-- run test for individual file -->

.\.venv\Scripts\python.exe -m pytest tests/api/test_auth_profile.py -v

.\.venv\Scripts\Activate.ps1; uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
