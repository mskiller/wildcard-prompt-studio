import requests
import socket
import time

def test_frontend_health():
    """Verify the frontend dev server is reachable."""
    # Wait for the port to become open (retry loop to avoid flakiness)
    max_retries = 15
    for attempt in range(max_retries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1.0)
            result = sock.connect_ex(('127.0.0.1', 5173))
            if result == 0:
                break
        time.sleep(1)
    else:
        assert False, "Frontend port 5173 is not open after 15 seconds"
        
    response = requests.get("http://127.0.0.1:5173")
    assert response.status_code == 200
