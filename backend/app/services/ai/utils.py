import os
from typing import List

def get_url_candidates(base_url: str = None, default_port: int = 5001) -> List[str]:
    """
    Generates candidate base URLs for connecting to local AI services (KoboldCpp, Ollama, ComfyUI).
    Ensures seamless connectivity whether running inside Docker containers or natively on host,
    and strips trailing slashes or redundant /v1 suffixes.
    """
    if not base_url:
        base_url = f"http://host.docker.internal:{default_port}"

    clean = base_url.rstrip('/')
    if clean.endswith('/v1'):
        clean = clean[:-3]

    candidates = [clean]

    # Detect container environment
    in_docker = os.path.exists('/.dockerenv') or os.getenv("DOCKER_CONTAINER") == "true" or os.getenv("KOBOLDCPP_HOST") is not None

    def add_cand(url_str: str):
        u = url_str.rstrip('/')
        if u.endswith('/v1'):
            u = u[:-3]
        if u not in candidates:
            candidates.append(u)

    if "localhost" in clean or "127.0.0.1" in clean:
        docker_host = clean.replace("localhost", "host.docker.internal").replace("127.0.0.1", "host.docker.internal")
        if in_docker:
            if docker_host not in candidates:
                candidates.insert(0, docker_host)
        else:
            add_cand(docker_host)

        add_cand(clean.replace("localhost", "127.0.0.1"))
        add_cand(clean.replace("127.0.0.1", "localhost"))
        add_cand(clean.replace("localhost", "172.17.0.1").replace("127.0.0.1", "172.17.0.1"))
        add_cand(clean.replace("localhost", "172.18.0.1").replace("127.0.0.1", "172.18.0.1"))
        add_cand(clean.replace("localhost", "172.19.0.1").replace("127.0.0.1", "172.19.0.1"))

    elif "host.docker.internal" in clean:
        add_cand(clean.replace("host.docker.internal", "localhost"))
        add_cand(clean.replace("host.docker.internal", "127.0.0.1"))
        add_cand(clean.replace("host.docker.internal", "172.17.0.1"))
        add_cand(clean.replace("host.docker.internal", "172.18.0.1"))
        add_cand(clean.replace("host.docker.internal", "172.19.0.1"))

    return candidates

