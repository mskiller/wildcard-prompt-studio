from app.services.wildcard_ast import WildcardASTEngine, serialize_ast_to_graph, deserialize_graph_to_ast

def test_ast_graph_serialization_roundtrip():
    engine = WildcardASTEngine()
    prompt = "{3$$red|1$$blue} __lighting__"
    ast = engine.parse(prompt)

    graph_dict = serialize_ast_to_graph(ast)
    assert graph_dict["type"] == "RootNode"
    assert len(graph_dict["children"]) == 3

    rebuilt_ast = deserialize_graph_to_ast(graph_dict)
    rebuilt_prompt = engine._unexpanded_str(rebuilt_ast)
    assert rebuilt_prompt == prompt

def test_matrix_engine_heatmap_scoring():
    from app.services.matrix_engine import MatrixEngine
    matrix_eng = MatrixEngine(wildcards={"color": ["red", "blue"]})
    prompt = "masterpiece, solo, 1girl, {red|blue} hair, by artist_name"
    scores = matrix_eng.analyze_heatmap_scores(prompt)

    assert scores["combinations_count"] == 2
    assert scores["avg_token_count"] > 0
    assert "artist" in scores["category_distribution"]
    assert "character" in scores["category_distribution"]

