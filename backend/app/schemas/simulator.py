from pydantic import BaseModel
from typing import Dict, List, Any, Optional

class SimulatorRequest(BaseModel):
    template: str
    iterations: int = 100

class SimulationResultItem(BaseModel):
    text: str
    count: int
    percentage: float

class SimulationResponse(BaseModel):
    success: bool
    error: Optional[str] = None
    iterations: Optional[int] = None
    unique_results: Optional[int] = None
    distribution: Optional[List[SimulationResultItem]] = None
    validation_report: Optional[Dict[str, Any]] = None

class GraphResponse(BaseModel):
    is_valid: bool
    cycles: List[List[str]]
    missing: List[str]
    graph: Dict[str, List[str]]
