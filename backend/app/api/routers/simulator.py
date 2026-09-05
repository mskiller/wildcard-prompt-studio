import os
from fastapi import APIRouter
from app.schemas.simulator import SimulatorRequest, SimulationResponse, GraphResponse
from app.services.wildcard_engine import WildcardEngine
from app.services.wildcard_graph import WildcardGraph
from app.services.simulator import Simulator

router = APIRouter()
WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "/workspace")

def get_engine() -> WildcardEngine:
    engine = WildcardEngine()
    engine.load_from_directory(os.path.join(WORKSPACE_DIR, "wildcards"))
    return engine

@router.get("/graph", response_model=GraphResponse)
def get_wildcard_graph():
    engine = get_engine()
    graph = WildcardGraph(engine.wildcards)
    return graph.get_validation_report()

from pydantic import BaseModel
from typing import List, Optional

class RecommendationsRequest(BaseModel):
    tags: List[str]
    top_k: Optional[int] = 5

@router.post("/run", response_model=SimulationResponse)
def run_simulation(request: SimulatorRequest):
    engine = get_engine()
    simulator = Simulator(engine)
    result = simulator.run_simulation(request.template, request.iterations)
    return result

@router.post("/tree")
def get_simulation_tree(request: SimulatorRequest):
    engine = get_engine()
    simulator = Simulator(engine)
    return simulator.build_ast_tree(request.template)

@router.post("/recommendations")
def get_tag_recommendations(request: RecommendationsRequest):
    from app.services.wildcard_graph import TagGraphService
    tag_service = TagGraphService()
    # Seed default co-occurrences for demo/runtime
    tag_service.add_cooccurrence(["cyberpunk", "neon", "city", "futuristic", "rain"])
    tag_service.add_cooccurrence(["portrait", "photorealistic", "soft lighting", "85mm"])
    return {"recommendations": tag_service.recommend(request.tags, top_k=request.top_k or 5)}

class ASTSerializeRequest(BaseModel):
    prompt: str

class ASTDeserializeRequest(BaseModel):
    graph: dict

@router.post("/ast/serialize")
def serialize_ast(request: ASTSerializeRequest):
    from app.services.wildcard_ast import WildcardASTEngine, serialize_ast_to_graph
    engine = WildcardASTEngine()
    ast = engine.parse(request.prompt)
    graph = serialize_ast_to_graph(ast)
    return {"graph": graph}

@router.post("/ast/deserialize")
def deserialize_ast(request: ASTDeserializeRequest):
    from app.services.wildcard_ast import WildcardASTEngine, deserialize_graph_to_ast
    engine = WildcardASTEngine()
    ast = deserialize_graph_to_ast(request.graph)
    unexpanded = engine._unexpanded_str(ast)
    return {"prompt": unexpanded, "ast": request.graph}



