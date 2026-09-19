import hmac
import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MAX_BODY = 1024 * 1024

SERVICES = {
    "prospex": "GE360_PROSPEX_URL",
    "suitecrm": "GE360_SUITECRM_URL",
    "n8n": "GE360_N8N_URL",
    "jarvis": "GE360_JARVIS_URL",
}

FORWARDS = {
    "/webhook/prospex": "N8N_PROSPEX_WEBHOOK_URL",
    "/webhook/mautic": "N8N_MAUTIC_WEBHOOK_URL",
}


def configured_services():
    return {name: bool(os.getenv(env_name, "").strip()) for name, env_name in SERVICES.items()}


class Handler(BaseHTTPRequestHandler):
    server_version = "GE360Bridge/0.1"

    def _json(self, status, payload):
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _authorized(self):
        expected = os.getenv("GE360_BRIDGE_TOKEN", "")
        supplied = self.headers.get("X-GE360-Token", "")
        return bool(expected) and hmac.compare_digest(expected, supplied)

    def do_GET(self):
        if self.path == "/health":
            self._json(200, {
                "service": "ge360-bridge",
                "status": "ok",
                "version": "0.1.0",
                "configured": configured_services(),
            })
            return
        self._json(404, {"error": "not_found"})

    def do_POST(self):
        if self.path not in FORWARDS:
            self._json(404, {"error": "not_found"})
            return

        if not self._authorized():
            self._json(401, {"error": "unauthorized"})
            return

        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0 or length > MAX_BODY:
            self._json(413, {"error": "invalid_body_size"})
            return

        try:
            body = self.rfile.read(length)
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._json(400, {"error": "invalid_json"})
            return

        target_env = FORWARDS[self.path]
        target = os.getenv(target_env, "").strip()
        if not target:
            self._json(503, {"error": "target_not_configured", "target": target_env})
            return

        source = self.path.rsplit("/", 1)[-1]
        outbound = json.dumps({
            "source": source,
            "payload": payload,
        }).encode("utf-8")

        request = urllib.request.Request(
            target,
            data=outbound,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "User-Agent": "GE360-Bridge/0.1",
                "X-GE360-Source": source,
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                response_body = response.read(65536)
                content_type = response.headers.get("Content-Type", "")
                self._json(200, {
                    "forwarded": True,
                    "status": response.status,
                    "content_type": content_type,
                    "response_bytes": len(response_body),
                })
        except urllib.error.HTTPError as exc:
            self._json(502, {"error": "upstream_http_error", "status": exc.code})
        except (urllib.error.URLError, TimeoutError):
            self._json(502, {"error": "upstream_unreachable"})

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args), flush=True)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8080), Handler)
    print("GE360 Bridge listening on :8080", flush=True)
    server.serve_forever()
