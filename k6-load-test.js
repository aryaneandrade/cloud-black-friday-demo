import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  stages: [
    { duration: "20s", target: 10 },
    { duration: "30s", target: 60 },
    { duration: "45s", target: 180 },
    { duration: "30s", target: 60 },
    { duration: "20s", target: 0 },
  ],
  thresholds: {
    http_req_failed: ["rate<0.05"],
    http_req_duration: ["p(95)<1500"],
  },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:8080";

export default function () {
  const clientId = `k6-${__VU}-${__ITER}`;
  const response = http.get(`${BASE_URL}/api/load?work_ms=160`, {
    headers: { "X-Demo-Client": clientId },
  });

  check(response, {
    "status 200": (r) => r.status === 200,
    "servidor identificado": (r) => Boolean(r.headers["X-Demo-Instance"]),
  });

  sleep(0.2);
}
