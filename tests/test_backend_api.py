import os
import requests

def test_backend_health():
    """Verify the backend health endpoint returns 200 OK."""
    url = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
    response = requests.get(f"{url}/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
