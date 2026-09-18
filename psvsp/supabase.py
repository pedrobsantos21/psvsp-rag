import json
import os
import urllib.request


def post(path: str, body, prefer: str = "") -> object:
    """POST JSON na API REST do Supabase (porta 443). Levanta em erro HTTP."""
    req = urllib.request.Request(
        f"{os.environ['SUPABASE_URL']}/rest/v1/{path}",
        data=json.dumps(body, ensure_ascii=False).encode(),
        headers={
            "apikey": os.environ["SUPABASE_SECRET_KEY"],
            "Content-Type": "application/json",
            "Prefer": prefer,
        },
    )
    with urllib.request.urlopen(req) as r:
        raw = r.read()
    return json.loads(raw) if raw else None
