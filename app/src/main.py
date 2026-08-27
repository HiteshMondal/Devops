"""Application entrypoint.

Run with: uvicorn src.main:app --host 0.0.0.0 --port $APP_PORT
(this is exactly what the Dockerfile's CMD does).
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .config import config
from .dsa import (
    BinarySearchTree,
    LinkedList,
    Trie,
    UnionFind,
    binary_search,
    bfs,
    dfs,
    dijkstra,
    merge_sort,
    quicksort,
)
from .sysdesign import (
    CircuitBreaker,
    ConsistentHashRing,
    LRUCache,
    RoundRobinBalancer,
    TokenBucketRateLimiter,
)

app = FastAPI(title=config.APP_NAME)

# In-memory singletons used purely to demonstrate the patterns via the API.
_lru_cache = LRUCache(capacity=5)
_rate_limiter = TokenBucketRateLimiter(capacity=5, refill_per_second=1)
_circuit_breaker = CircuitBreaker(failure_threshold=3, reset_timeout_seconds=15)


# Health

@app.get("/health")
def health():
    """Liveness probe — is the process up?"""
    return {"status": "ok", "app": config.APP_NAME, "env": config.APP_ENV}


@app.get("/ready")
def ready():
    """Readiness probe — is the app ready to serve traffic?"""
    return {"status": "ready"}


@app.get("/config")
def get_config():
    """Non-sensitive runtime configuration (secrets are never returned)."""
    return {
        "app_name": config.APP_NAME,
        "app_env": config.APP_ENV,
        "app_port": config.APP_PORT,
        "log_level": config.LOG_LEVEL,
        "db_host": config.DB_HOST,
        "db_port": config.DB_PORT,
        "db_name": config.DB_NAME,
    }


# ---DSA

class IntList(BaseModel):
    items: list[int]


class SearchRequest(BaseModel):
    items: list[int]
    target: int


@app.post("/dsa/sort/quicksort")
def sort_quicksort(body: IntList):
    return {"sorted": quicksort(body.items)}


@app.post("/dsa/sort/merge-sort")
def sort_merge(body: IntList):
    return {"sorted": merge_sort(body.items)}


@app.post("/dsa/search/binary")
def search_binary(body: SearchRequest):
    return {"index": binary_search(sorted(body.items), body.target)}


class GraphRequest(BaseModel):
    edges: list[tuple[str, str, int]]  # (from, to, weight)
    start: str


def _build_graph(edges: list[tuple[str, str, int]]) -> dict:
    graph: dict = {}
    for src, dst, weight in edges:
        graph.setdefault(src, []).append((dst, weight))
        graph.setdefault(dst, []).append((src, weight))
    return graph


@app.post("/dsa/graph/bfs")
def graph_bfs(body: GraphRequest):
    return {"order": bfs(_build_graph(body.edges), body.start)}


@app.post("/dsa/graph/dfs")
def graph_dfs(body: GraphRequest):
    return {"order": dfs(_build_graph(body.edges), body.start)}


@app.post("/dsa/graph/dijkstra")
def graph_dijkstra(body: GraphRequest):
    return {"distances": dijkstra(_build_graph(body.edges), body.start)}


class TrieRequest(BaseModel):
    words: list[str]
    query: str


@app.post("/dsa/trie/search")
def trie_search(body: TrieRequest):
    trie = Trie()
    for w in body.words:
        trie.insert(w)
    return {"found": trie.search(body.query)}


@app.post("/dsa/linked-list/reverse")
def linked_list_reverse(body: IntList):
    ll = LinkedList()
    for x in body.items:
        ll.push(x)
    ll.reverse()
    return {"reversed": ll.to_list()}


@app.post("/dsa/bst/inorder")
def bst_inorder(body: IntList):
    tree = BinarySearchTree()
    for x in body.items:
        tree.insert(x)
    return {"inorder": tree.inorder()}


class UnionFindRequest(BaseModel):
    items: list[str]
    unions: list[tuple[str, str]]
    a: str
    b: str


@app.post("/dsa/union-find/connected")
def union_find_connected(body: UnionFindRequest):
    uf = UnionFind(body.items)
    for a, b in body.unions:
        uf.union(a, b)
    return {"connected": uf.connected(body.a, body.b)}


# ------------------------------------------------------------- System Design

@app.get("/sysdesign/rate-limiter/check")
def rate_limiter_check():
    return {"allowed": _rate_limiter.allow()}


class CacheEntry(BaseModel):
    key: str
    value: str


@app.post("/sysdesign/cache/put")
def cache_put(body: CacheEntry):
    _lru_cache.put(body.key, body.value)
    return {"size": len(_lru_cache)}


@app.get("/sysdesign/cache/get/{key}")
def cache_get(key: str):
    value = _lru_cache.get(key)
    if value is None:
        raise HTTPException(status_code=404, detail="key not found or evicted")
    return {"key": key, "value": value}


@app.post("/sysdesign/circuit-breaker/success")
def circuit_success():
    _circuit_breaker.record_success()
    return {"state": _circuit_breaker.state.value}


@app.post("/sysdesign/circuit-breaker/failure")
def circuit_failure():
    _circuit_breaker.record_failure()
    return {"state": _circuit_breaker.state.value}


@app.get("/sysdesign/circuit-breaker/state")
def circuit_state():
    return {"state": _circuit_breaker.state.value, "allow_request": _circuit_breaker.allow_request()}


class HashRingRequest(BaseModel):
    nodes: list[str]
    key: str


@app.post("/sysdesign/consistent-hash/lookup")
def consistent_hash_lookup(body: HashRingRequest):
    ring = ConsistentHashRing(body.nodes)
    return {"node": ring.get_node(body.key)}


class BalancerRequest(BaseModel):
    backends: list[str]
    requests: int = 1


@app.post("/sysdesign/load-balancer/round-robin")
def load_balancer_round_robin(body: BalancerRequest):
    balancer = RoundRobinBalancer(body.backends)
    return {"assignments": [balancer.next_backend() for _ in range(body.requests)]}