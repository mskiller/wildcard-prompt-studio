import pytest
import sys
sys.path.insert(0, "/app")
from fastapi.testclient import TestClient
from main import app
from app.services.wildcard_engine import WildcardEngine
from app.services.wildcard_graph import WildcardGraph
from app.services.simulator import Simulator

client = TestClient(app)
BASE_URL = "/api/v1/simulator"

def test_wildcard_graph():
    wildcards = {
        "color": ["red", "blue"],
        "animal": ["__color__ dog", "cat"],
        "cycle_a": ["__cycle_b__"],
        "cycle_b": ["__cycle_a__"]
    }
    graph = WildcardGraph(wildcards)
    report = graph.get_validation_report()
    
    assert not report["is_valid"]
    assert "cycle_a" in report["cycles"][0]
    assert "cycle_b" in report["cycles"][0]

def test_simulator():
    engine = WildcardEngine({
        "color": ["red", "blue"]
    })
    simulator = Simulator(engine)
    
    result = simulator.run_simulation("a __color__ car", iterations=100)
    assert result["success"]
    assert result["iterations"] == 100
    assert result["unique_results"] <= 2
    
    texts = [item["text"] for item in result["distribution"]]
    assert "a red car" in texts or "a blue car" in texts

def test_simulator_api_run():
    resp = client.post(f"{BASE_URL}/run", json={"template": "hello {world|there}", "iterations": 50})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"]
    assert data["iterations"] == 50
    assert data["unique_results"] <= 2
