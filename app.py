import hashlib
from datetime import datetime, timedelta, timezone

import boto3
import json
import os
import socket
import time
import uuid
from collections import deque
from threading import Lock, Thread
from urllib.error import URLError
from urllib.request import Request, urlopen

import psutil
from flask import Flask, jsonify, render_template, request

try:
    import redis
except ImportError:
    redis = None


app = Flask(__name__)

STORE_CONFIG_PATH = os.getenv("STORE_CONFIG_PATH", "/app/data/store.json")
COUNTDOWN_SECONDS_DEFAULT = 10
INSTANCE_HEARTBEAT_SECONDS = 2
INSTANCE_STALE_SECONDS = 15
IMDS_BASE_URL = "http://169.254.169.254/latest"
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
CLOUDWATCH_CPU_POLL_SECONDS = 15


def load_store_config():
    with open(STORE_CONFIG_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def imds_get(path, timeout=1.0):
    """Read EC2 metadata through IMDSv2.

    Returns None outside EC2 or when metadata is unavailable.
    """
    try:
        token_request = Request(
            f"{IMDS_BASE_URL}/api/token",
            method="PUT",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"},
        )
        with urlopen(token_request, timeout=timeout) as response:
            token = response.read().decode("utf-8").strip()

        metadata_request = Request(
            f"{IMDS_BASE_URL}/meta-data/{path}",
            headers={"X-aws-ec2-metadata-token": token},
        )
        with urlopen(metadata_request, timeout=timeout) as response:
            return response.read().decode("utf-8").strip()
    except (OSError, URLError, TimeoutError, ValueError):
        return None


def resolve_instance_identity():
    """Prefer environment overrides, then EC2 metadata, then local fallbacks."""
    instance_id = os.getenv("INSTANCE_ID") or imds_get("instance-id")
    private_ip = os.getenv("INSTANCE_IP") or imds_get("local-ipv4")
    instance_name = os.getenv("INSTANCE_NAME", "cloud-black-friday-demo-app-asg")

    if not instance_id:
        instance_id = socket.gethostname()

    if not private_ip:
        try:
            private_ip = socket.gethostbyname(socket.gethostname())
        except OSError:
            private_ip = "indisponível"

    return instance_id, private_ip, instance_name


STORE_CONFIG = load_store_config()
APP_NAME = os.getenv("APP_NAME", STORE_CONFIG["store"]["name"])
REDIS_URL = os.getenv("REDIS_URL", "")
COUNTDOWN_SECONDS = int(
    os.getenv(
        "COUNTDOWN_SECONDS",
        str(STORE_CONFIG["store"].get("countdown_seconds", COUNTDOWN_SECONDS_DEFAULT)),
    )
)
INSTANCE_ID, INSTANCE_IP, INSTANCE_NAME = resolve_instance_identity()

try:
    cloudwatch_client = boto3.client("cloudwatch", region_name=AWS_REGION)
except Exception:
    cloudwatch_client = None

redis_client = None
if REDIS_URL and redis:
    try:
        redis_client = redis.Redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
            health_check_interval=15,
        )
        redis_client.ping()
    except Exception:
        redis_client = None

lock = Lock()
local_total_requests = 0
local_active_requests = 0
recent_clients = {}
recent_request_times = deque(maxlen=500)
recent_request_events = deque(maxlen=5000)
latest_cpu_percent = 0.0
last_cloudwatch_cpu_check = 0.0

local_demo_state = {
    "phase": "normal",
    "countdown_started_at": None,
    "load_mode": False,
    "updated_at": time.time(),
}


def get_ec2_cpu():
    """Return the EC2 CPUUtilization metric from CloudWatch.

    Outside EC2, without IAM permission, or while CloudWatch has no fresh
    datapoint, fall back to psutil so the local environment remains usable.
    """
    fallback_cpu = psutil.cpu_percent(interval=0.2)

    if not INSTANCE_ID.startswith("i-") or cloudwatch_client is None:
        return round(fallback_cpu, 1)

    try:
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(minutes=3)

        response = cloudwatch_client.get_metric_statistics(
            Namespace="AWS/EC2",
            MetricName="CPUUtilization",
            Dimensions=[{"Name": "InstanceId", "Value": INSTANCE_ID}],
            StartTime=start_time,
            EndTime=end_time,
            Period=60,
            Statistics=["Average"],
        )

        datapoints = sorted(
            response.get("Datapoints", []),
            key=lambda item: item["Timestamp"],
        )

        if not datapoints:
            return round(fallback_cpu, 1)

        return round(float(datapoints[-1]["Average"]), 1)
    except Exception:
        return round(fallback_cpu, 1)


def state_key():
    return "demo:state:v5"


def get_demo_state():
    if redis_client:
        raw = redis_client.hgetall(state_key())
        if raw:
            return {
                "phase": raw.get("phase", "normal"),
                "countdown_started_at": (
                    float(raw["countdown_started_at"])
                    if raw.get("countdown_started_at")
                    else None
                ),
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
        return

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
    request_cutoff = now - 30

    for client_id in [key for key, seen_at in recent_clients.items() if seen_at < client_cutoff]:
        recent_clients.pop(client_id, None)

    while recent_request_events and recent_request_events[0] < request_cutoff:
        recent_request_events.popleft()


def register_instance(cpu_percent):
    if not redis_client:
        return

    now = time.time()
    details = json.dumps(
        {
            "id": INSTANCE_ID,
            "name": INSTANCE_NAME,
            "ip": INSTANCE_IP,
            "cpu": round(cpu_percent, 1),
            "last_seen": now,
        },
        ensure_ascii=False,
    )

    pipe = redis_client.pipeline()
    pipe.zadd("demo:instances", {INSTANCE_ID: now})
    pipe.hset("demo:instance_details", INSTANCE_ID, details)
    pipe.expire("demo:instances", 120)
    pipe.expire("demo:instance_details", 120)
    pipe.execute()


def get_instances(cpu_percent):
    if not redis_client:
        return [
            {
                "id": INSTANCE_ID,
                "name": INSTANCE_NAME,
                "ip": INSTANCE_IP,
                "cpu": round(cpu_percent, 1),
            }
        ]

    now = time.time()
    stale_ids = redis_client.zrangebyscore(
        "demo:instances",
        0,
        now - INSTANCE_STALE_SECONDS,
    )

    pipe = redis_client.pipeline()
    pipe.zremrangebyscore("demo:instances", 0, now - INSTANCE_STALE_SECONDS)
    if stale_ids:
        pipe.hdel("demo:instance_details", *stale_ids)
    pipe.execute()

    ids = redis_client.zrange("demo:instances", 0, -1)
    details = redis_client.hmget("demo:instance_details", ids) if ids else []

    result = []
    for instance_id, raw_detail in zip(ids, details):
        if not raw_detail:
            continue

        try:
            detail = json.loads(raw_detail)
        except (TypeError, json.JSONDecodeError):
            continue

        result.append(
            {
                "id": instance_id,
                "name": detail.get("name", "EC2"),
                "ip": detail.get("ip", "indisponível"),
                "cpu": round(float(detail.get("cpu", 0.0)), 1),
            }
        )

    if result:
        return result

    return [
        {
            "id": INSTANCE_ID,
            "name": INSTANCE_NAME,
            "ip": INSTANCE_IP,
            "cpu": round(cpu_percent, 1),
        }
    ]


def heartbeat_worker():
    """Publica no Redis a CPU atual da instância a cada dois segundos."""
    global latest_cpu_percent

    # Inicializa o cálculo do psutil para que a primeira leitura seja válida.
    psutil.cpu_percent(interval=None)

    while True:
        try:
            # Mede a utilização real da CPU durante uma janela de 1 segundo.
            cpu_percent = round(
                psutil.cpu_percent(interval=1.0),
                1,
            )

            with lock:
                latest_cpu_percent = cpu_percent

            # Cada EC2 publica sua própria CPU no Redis.
            register_instance(cpu_percent)

        except Exception:
            pass

        # A medição já consome aproximadamente 1 segundo.
        time.sleep(
            max(
                0,
                INSTANCE_HEARTBEAT_SECONDS - 1,
            )
        )

Thread(target=heartbeat_worker, name="instance-heartbeat", daemon=True).start()


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
            (
                time.perf_counter()
                - getattr(request, "_started_at", time.perf_counter())
            )
            * 1000,
            1,
        )

        response.headers["X-Demo-Instance"] = INSTANCE_ID
        response.headers["X-Demo-Instance-Name"] = INSTANCE_NAME
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
    featured = next(
        (product for product in STORE_CONFIG["products"] if product.get("featured")),
        STORE_CONFIG["products"][0],
    )

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

    with lock:
        cpu = latest_cpu_percent
        cleanup_local_data()
        local_users = len(recent_clients)
        local_total = local_total_requests
        local_active = local_active_requests
        local_recent_requests = len(recent_request_events)
        local_rps = round(
            local_recent_requests / 30,
            1,
        )
        average_response_ms = (
            round(sum(recent_request_times) / len(recent_request_times), 1)
            if recent_request_times
            else 0
        )

    register_instance(cpu)

    if redis_client:
        now = time.time()
        redis_client.zremrangebyscore("demo:clients", 0, now - 30)
        redis_client.zremrangebyscore(
            "demo:request_events",
            0,
            now - 30,
        )

        users = int(redis_client.zcard("demo:clients"))
        total = int(redis_client.get("demo:total_requests") or local_total)
        active = max(
            0,
            int(redis_client.get("demo:active_requests") or local_active),
        )
        recent_requests = int(
            redis_client.zcard(
                "demo:request_events"
            )
        )
        requests_per_second = round(
            recent_requests / 30,
            1,
        )
    else:
        users = local_users
        total = local_total
        active = local_active
        recent_requests = local_recent_requests
        requests_per_second = local_rps

    instances = get_instances(cpu)
    average_cpu = round(
        sum(instance["cpu"] for instance in instances) / max(1, len(instances)),
        1,
    )

    if state["load_mode"] and users < 2:
        status_label = "Carga real ativa"
    elif average_cpu >= 75 or requests_per_second >= 35:
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
        requests_per_second=requests_per_second,
        recent_requests=recent_requests,
        total_requests=total,
        average_cpu=average_cpu,
        average_response_ms=average_response_ms,
        instance_id=INSTANCE_ID,
        instance_name=INSTANCE_NAME,
        instance_ip=INSTANCE_IP,
        instances=instances,
        active_instance_count=len(instances),
        status_label=status_label,
        metrics_mode="redis-cloudwatch" if redis_client else "local-cloudwatch",
    )


@app.post("/api/demo/start-black-friday")
def start_black_friday():
    state = get_demo_state()
    state["phase"] = "countdown"
    state["countdown_started_at"] = time.time()
    save_demo_state(state)

    return jsonify(
        ok=True,
        phase="countdown",
        seconds=COUNTDOWN_SECONDS,
    )


@app.post("/api/demo/toggle-load")
def toggle_load():
    state = get_demo_state()
    state["load_mode"] = not state.get("load_mode", False)
    save_demo_state(state)

    return jsonify(
        ok=True,
        load_mode=state["load_mode"],
    )


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
        redis_client.delete(
            "demo:total_requests",
            "demo:active_requests",
            "demo:clients",
            "demo:request_events",
        )

    with lock:
        local_total_requests = 0
        local_active_requests = 0
        recent_clients.clear()
        recent_request_times.clear()
        recent_request_events.clear()

    return jsonify(ok=True)


@app.route("/api/load")
def load():
    """Perform real CPU-bound work for a bounded amount of time."""
    try:
        requested_work_ms = int(request.args.get("work_ms", "300"))
    except ValueError:
        requested_work_ms = 300

    work_ms = min(max(requested_work_ms, 20), 1500)
    deadline = time.perf_counter() + (work_ms / 1000)
    digest = b"cloud-black-friday-demo"

    while time.perf_counter() < deadline:
        digest = hashlib.sha256(digest).digest()

    return jsonify(
        ok=True,
        work_ms=work_ms,
        checksum=digest.hex()[:16],
        instance_id=INSTANCE_ID,
        instance_name=INSTANCE_NAME,
        instance_ip=INSTANCE_IP,
    )


@app.route("/health")
def health():
    return jsonify(
        status="ok",
        instance_id=INSTANCE_ID,
        instance_ip=INSTANCE_IP,
    ), 200


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8080")),
    )