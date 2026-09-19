import hmac
import html
import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MAX_BODY = 1024 * 1024

SERVICES = {
    "mautic": "GE360_MAUTIC_URL",
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


def probe(url):
    if not url:
        return {"configured": False, "reachable": False, "status": None}

    request = urllib.request.Request(url, method="GET", headers={"User-Agent": "GE360-Bridge/0.2"})
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            return {"configured": True, "reachable": True, "status": response.status}
    except urllib.error.HTTPError as exc:
        # Authentication failures still prove that the service is alive.
        return {"configured": True, "reachable": True, "status": exc.code}
    except (urllib.error.URLError, TimeoutError, ValueError):
        return {"configured": True, "reachable": False, "status": None}


def service_status():
    return {
        name: probe(os.getenv(env_name, "").strip())
        for name, env_name in SERVICES.items()
    }


def dashboard_html():
    cards = "".join(
        f"""
        <article class="card" data-service="{html.escape(name)}">
          <div class="dot pending"></div>
          <div>
            <strong>{html.escape(name.upper())}</strong>
            <span>controllo...</span>
          </div>
        </article>
        """
        for name in SERVICES
    )

    return f"""<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GE360 Mautic Control Center</title>
<style>
:root {{ color-scheme: dark; font-family: Inter, system-ui, sans-serif; }}
* {{ box-sizing: border-box; }}
body {{ margin:0; min-height:100vh; background:#0b0f17; color:#edf2f7; }}
main {{ width:min(1050px,92vw); margin:0 auto; padding:48px 0; }}
header {{ display:flex; justify-content:space-between; gap:24px; align-items:flex-end; margin-bottom:30px; }}
.brand {{ font-size:12px; letter-spacing:.22em; text-transform:uppercase; opacity:.65; }}
h1 {{ margin:.35rem 0 0; font-size:clamp(30px,5vw,56px); }}
.badge {{ padding:8px 12px; border:1px solid #263245; border-radius:999px; color:#a9b7ca; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:14px; }}
.card {{ display:flex; gap:13px; align-items:center; min-height:105px; padding:20px; border:1px solid #202b3a; border-radius:18px; background:#111823; box-shadow:0 12px 35px rgba(0,0,0,.18); }}
.card strong {{ display:block; margin-bottom:7px; font-size:14px; letter-spacing:.08em; }}
.card span {{ color:#8997aa; font-size:13px; }}
.dot {{ width:13px; height:13px; border-radius:50%; flex:0 0 13px; box-shadow:0 0 18px currentColor; }}
.dot.ok {{ background:#4ade80; color:#4ade80; }}
.dot.bad {{ background:#fb7185; color:#fb7185; }}
.dot.off {{ background:#64748b; color:#64748b; }}
.dot.pending {{ background:#fbbf24; color:#fbbf24; }}
footer {{ margin-top:30px; color:#66758a; font-size:13px; }}
code {{ color:#b8c7da; }}
</style>
</head>
<body>
<main>
<header>
  <div><div class="brand">GE360 • Communication Hub</div><h1>Mautic Control Center</h1></div>
  <div class="badge" id="updated">avvio...</div>
</header>
<section class="grid">{cards}</section>
<footer>Bridge <code>v0.2.0</code> · refresh automatico ogni 10 secondi · nessuna credenziale viene mostrata.</footer>
</main>
<script>
async function refresh() {{
  try {{
    const r = await fetch('/api/status', {{cache:'no-store'}});
    const data = await r.json();
    for (const [name, state] of Object.entries(data.services)) {{
      const card = document.querySelector('[data-service="'+name+'"]');
      if (!card) continue;
      const dot = card.querySelector('.dot');
      const text = card.querySelector('span');
      dot.className = 'dot ' + (!state.configured ? 'off' : state.reachable ? 'ok' : 'bad');
      text.textContent = !state.configured ? 'non configurato' : state.reachable ? 'online · HTTP ' + state.status : 'non raggiungibile';
    }}
    document.getElementById('updated').textContent = 'aggiornato ora';
  }} catch (_) {{
    document.getElementById('updated').textContent = 'bridge non raggiungibile';
  }}
}}
refresh();
setInterval(refresh, 10000);
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    server_version = "GE360Bridge/0.2"

    def _json(self, status, payload):
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _html(self, status, page):
        data = page.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _authorized(self):
        expected = os.getenv("GE360_BRIDGE_TOKEN", "")
        supplied = self.headers.get("X-GE360-Token", "")
        return bool(expected) and hmac.compare_digest(expected, supplied)

    def do_GET(self):
        if self.path == "/":
            self._html(200, dashboard_html())
            return
        if self.path == "/health":
            self._json(200, {
                "service": "ge360-bridge",
                "status": "ok",
                "version": "0.2.0",
                "configured": configured_services(),
            })
            return
        if self.path == "/api/status":
            self._json(200, {
                "service": "ge360-bridge",
                "version": "0.2.0",
                "services": service_status(),
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
                "User-Agent": "GE360-Bridge/0.2",
                "X-GE360-Source": source,
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                response_body = response.read(65536)
                self._json(200, {
                    "forwarded": True,
                    "status": response.status,
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
