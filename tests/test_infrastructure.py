# tests/test_infrastructure.py
import socket

def test_postgres_port_open():
    """Verify PostgreSQL is running and port 5432 is open."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1.0)
        result = sock.connect_ex(('127.0.0.1', 5432))
        assert result == 0, "PostgreSQL port 5432 is not open"

def test_redis_port_open():
    """Verify Redis is running and port 6379 is open."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1.0)
        result = sock.connect_ex(('127.0.0.1', 6379))
        assert result == 0, "Redis port 6379 is not open"
