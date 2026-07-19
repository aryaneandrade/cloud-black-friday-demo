import os
import json
import socket
import time
import uuid
from collections import deque
from threading import Lock

import psutil
from flask import Flask, jsonify, render_template, request

try:
    import redis
except ImportError:
    redis = None

app = Flask(__name__)

STORE_CONFIG_PATH = os.getenv("STORE_CONFIG_PATH", "/app/data/store.json")

def load_store_config():
    with open(STORE_CONFIG_PATH, "r", encoding="utf-8") as file:
        return json.load(file)

STORE_CONFIG = load_store_config()
APP_NAME = os.getenv("APP_NAME", STORE_CONFIG["store"]["name"])
REDIS_URL = os.getenv("REDIS_URL", "")
INSTANCE_ID = os.getenv("INSTANCE_ID", socket.gethostname())
INSTANCE_IP = os.getenv("INSTANCE_IP", "")
COUNTDOWN_SECONDS = int(os.getenv("COUNTDOWN_SECONDS", str(STORE_CONFIG["store"].get("countdown_seconds", 10))))

if not INSTANCE_IP:
    try:
        INSTANCE_IP = socket.gethostbyname(socket.gethostname())
    except OSError:
        INSTANCE_IP = "indisponível"

redis_client = None
if REDIS_URL and redis:
    try:
        redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.ping()
    except Exception:
        redis_client = None

lock = Lock()
started_at = time.time()
local_total_requests = 0
local_active_requests = 0
recent_clients = {}
recent_request_times = deque(maxlen=500)
recent_request_events = deque(maxlen=5000)

local_demo_state = {
    "phase": "normal",
    "countdown_started_at": None,
    "load_mode": False,
    "updated_at": time.time(),
}


def state_key():
    return "demo:state:v4"


def get_demo_state():
    if redis_client:
        raw = redis_client.hgetall(state_key())
        if raw:
            return {
                "phase": raw.get("phase", "normal"),
                "countdown_started_at": float(raw["countdown_started_at"]) if raw.get("countdown_started_at") else None,
                "load_mode": raw.get("load_mode", "0") == "1",
                "updated_at": float(raw.get("updated_at", time.time())),
            }
    with lock:
        return dict(local_demo_state)


def save_demo_state(state):
    state["updated_at"] = time.time()
    if redis_client:
        redis_client.hset(
            state_key(),
            mapping={
                "phase": state.get("phase", "normal"),
                "countdown_started_at": state.get("countdown_started_at") or "",
                "load_mode": "1" if state.get("load_mode") else "0",
                "updated_at": state["updated_at"],
            },
        )
    else:
        with lock:
            local_demo_state.update(state)


def resolve_demo_state():
    state = get_demo_state()
    if state["phase"] == "countdown" and state["countdown_started_at"]:
        elapsed = time.time() - state["countdown_started_at"]
        remaining = max(0, COUNTDOWN_SECONDS - int(elapsed))
        if elapsed >= COUNTDOWN_SECONDS:
            state["phase"] = "black_friday"
            state["countdown_started_at"] = None
            save_demo_state(state)
            remaining = 0
    else:
        remaining = COUNTDOWN_SECONDS if state["phase"] == "normal" else 0
    state["seconds_remaining"] = remaining
    return state


def cleanup_local_data():
    now = time.time()
    client_cutoff = now - 30
    request_cutoff = now - 10

    for client_id in [k for k, v in recent_clients.items() if v < client_cutoff]:
        recent_clients.pop(client_id, None)

    while recent_request_events and recent_request_events[0] < request_cutoff:
        recent_request_events.popleft()


def register_instance(cpu_percent):
    if not redis_client:
        return
    now = time.time()
    redis_client.zadd("demo:instances", {INSTANCE_ID: now})
    redis_client.hset("demo:instance_details", INSTANCE_ID, f"{INSTANCE_IP}|{cpu_percent:.1f}")
    redis_client.expire("demo:instances", 120)
    redis_client.expire("demo:instance_details", 120)


def get_instances(cpu_percent):
    if not redis_client:
        return [{"id": INSTANCE_ID, "ip": INSTANCE_IP, "cpu": round(cpu_percent, 1)}]

    now = time.time()
    redis_client.zremrangebyscore("demo:instances", 0, now - 15)
    ids = redis_client.zrange("demo:instances", 0, -1)
    details = redis_client.hmget("demo:instance_details", ids) if ids else []

    result = []
    for instance_id, detail in zip(ids, details):
        ip = "indisponível"
        cpu = 0.0
        if detail:
            parts = detail.split("|", 1)
            ip = parts[0]
            if len(parts) > 1:
                try:
                    cpu = float(parts[1])
                except ValueError:
                    cpu = 0.0
        result.append({"id": instance_id, "ip": ip, "cpu": round(cpu, 1)})

    return result or [{"id": INSTANCE_ID, "ip": INSTANCE_IP, "cpu": round(cpu_percent, 1)}]


@app.before_request
def before_request():
    global local_total_requests, local_active_requests
    request._started_at = time.perf_counter()

    if request.path.startswith("/static/"):
        return None

    now = time.time()
    with lock:
        local_total_requests += 1
        local_active_requests += 1
        recent_request_events.append(now)

    if redis_client:
        pipe = redis_client.pipeline()
        pipe.incr("demo:total_requests")
        pipe.incr("demo:active_requests")
        pipe.expire("demo:active_requests", 10)
        pipe.zadd("demo:request_events", {f"{now:.6f}:{uuid.uuid4()}": now})
        pipe.expire("demo:request_events", 120)
        pipe.execute()

    client_id = request.headers.get("X-Demo-Client") or request.cookies.get("demo_client_id")
    if client_id:
        with lock:
            recent_clients[client_id] = now
            cleanup_local_data()

        if redis_client:
            redis_client.zadd("demo:clients", {client_id: now})
            redis_client.zremrangebyscore("demo:clients", 0, now - 30)
            redis_client.expire("demo:clients", 120)


@app.after_request
def after_request(response):
    global local_active_requests

    if not request.path.startswith("/static/"):
        elapsed_ms = round(
            (time.perf_counter() - getattr(request, "_started_at", time.perf_counter())) * 1000,
            1,
        )

        response.headers["X-Demo-Instance"] = INSTANCE_ID
        response.headers["X-Demo-Instance-IP"] = INSTANCE_IP
        response.headers["X-Response-Time-Ms"] = str(elapsed_ms)

        with lock:
            local_active_requests = max(0, local_active_requests - 1)
            recent_request_times.append(elapsed_ms)

        if redis_client:
            redis_client.decr("demo:active_requests")

    if not request.cookies.get("demo_client_id"):
        response.set_cookie(
            "demo_client_id",
            str(uuid.uuid4()),
            max_age=86400,
            httponly=False,
            samesite="Lax",
        )
    return response


@app.route("/")
def index():
    featured = next((p for p in STORE_CONFIG["products"] if p.get("featured")), STORE_CONFIG["products"][0])
    return render_template(
        "index.html",
        app_name=APP_NAME,
        store=STORE_CONFIG["store"],
        hero=STORE_CONFIG["hero"],
        featured=featured,
        products=STORE_CONFIG["products"],
    )


@app.route("/api/status")
def status():
    state = resolve_demo_state()
    cpu = psutil.cpu_percent(interval=None)
    register_instance(cpu)

    with lock:
        cleanup_local_data()
        local_users = len(recent_clients)
        local_total = local_total_requests
        local_active = local_active_requests
        local_rps = round(len(recent_request_events) / 10, 1)
        avg_ms = round(sum(recent_request_times) / len(recent_request_times), 1) if recent_request_times else 0

    if redis_client:
        now = time.time()
        redis_client.zremrangebyscore("demo:clients", 0, now - 30)
        redis_client.zremrangebyscore("demo:request_events", 0, now - 10)
        users = int(redis_client.zcard("demo:clients"))
        total = int(redis_client.get("demo:total_requests") or local_total)
        active = max(0, int(redis_client.get("demo:active_requests") or local_active))
        rps = round(redis_client.zcard("demo:request_events") / 10, 1)
    else:
        users = local_users
        total = local_total
        active = local_active
        rps = local_rps

    instances = get_instances(cpu)
    average_cpu = round(sum(item["cpu"] for item in instances) / max(1, len(instances)), 1)

    if state["load_mode"] and users < 2:
        status_label = "Carga controlada ativa"
    elif average_cpu >= 75 or rps >= 35:
        status_label = "Alto volume de acessos"
    elif state["phase"] == "black_friday":
        status_label = "Black Friday em andamento"
    else:
        status_label = "Operação normal"

    return jsonify(
        phase=state["phase"],
        load_mode=state["load_mode"],
        seconds_remaining=state["seconds_remaining"],
        active_users=users,
        active_requests=active,
        requests_per_second=rps,
        total_requests=total,
        average_cpu=average_cpu,
        average_response_ms=avg_ms,
        instance_id=INSTANCE_ID,
        instance_ip=INSTANCE_IP,
        active_instance_count=len(instances),
        status_label=status_label,
        metrics_mode="redis" if redis_client else "local",
    )


@app.post("/api/demo/start-black-friday")
def start_black_friday():
    state = get_demo_state()
    state["phase"] = "countdown"
    state["countdown_started_at"] = time.time()
    save_demo_state(state)
    return jsonify(ok=True, phase="countdown", seconds=COUNTDOWN_SECONDS)


@app.post("/api/demo/toggle-load")
def toggle_load():
    state = get_demo_state()
    state["load_mode"] = not state.get("load_mode", False)
    save_demo_state(state)
    return jsonify(ok=True, load_mode=state["load_mode"])


@app.post("/api/demo/reset")
def reset_demo():
    global local_total_requests, local_active_requests
    save_demo_state(
        {
            "phase": "normal",
            "countdown_started_at": None,
            "load_mode": False,
        }
    )

    if redis_client:
        keys = [
            "demo:total_requests",
            "demo:active_requests",
            "demo:clients",
            "demo:request_events",
        ]
        redis_client.delete(*keys)

    with lock:
        local_total_requests = 0
        local_active_requests = 0
        recent_clients.clear()
        recent_request_times.clear()
        recent_request_events.clear()

    return jsonify(ok=True)


@app.route("/api/load")
def load():
    work_ms = min(max(int(request.args.get("work_ms", "150")), 10), 750)
    deadline = time.perf_counter() + (work_ms / 1000)
    value = 0

    while time.perf_counter() < deadline:
        value = (value * 33 + 17) % 1000003

    return jsonify(
        ok=True,
        checksum=value,
        instance_id=INSTANCE_ID,
        instance_ip=INSTANCE_IP,
    )


@app.route("/health")
def health():
    return jsonify(status="ok", instance_id=INSTANCE_ID), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
