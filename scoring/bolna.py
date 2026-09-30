"""Tiny Bolna API client plus the safety rails every script shares.

Standard library only. Docs: https://www.bolna.ai/docs/api-reference/introduction
Base URL https://api.bolna.ai, auth header "Authorization: Bearer <key>".
"""
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent
BASE = "https://api.bolna.ai"
TERMINAL = {"completed", "no-answer", "busy", "failed", "canceled", "cancelled",
            "stopped", "error", "balance-low"}


def load_env():
    """Read .env (KEY=VALUE lines) without printing anything from it."""
    env = {}
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    for k in list(env):
        env[k] = os.environ.get(k, env[k])
    return env


ENV = load_env()


def setting(name, default=None, required=False):
    v = ENV.get(name) or os.environ.get(name) or default
    if required and not v:
        sys.exit(f"Missing {name}. Put it in {ROOT / '.env'} (see .env.example).")
    return v


def _req(method, path, body=None, retries=5):
    key = setting("BOLNA_API_KEY", required=True)
    data = json.dumps(body).encode() if body is not None else None
    for attempt in range(retries):
        r = urllib.request.Request(BASE + path, data=data, method=method, headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        })
        try:
            with urllib.request.urlopen(r, timeout=60) as resp:
                raw = resp.read().decode() or "{}"
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            detail = e.read().decode(errors="replace")[:800]
            raise SystemExit(f"Bolna API {method} {path} -> HTTP {e.code}: {detail}")
    raise SystemExit("Rate limited too many times.")


def get(path):
    return _req("GET", path)


def post(path, body=None):
    return _req("POST", path, body if body is not None else {})


def put(path, body):
    return _req("PUT", path, body)


# ---------- phone-number guard ----------

E164 = re.compile(r"^\+[1-9]\d{7,14}$")


def verified_numbers():
    raw = setting("VERIFIED_NUMBERS", required=True)
    nums = [n.strip() for n in raw.split(",") if n.strip()]
    bad = [n for n in nums if not E164.match(n)]
    if bad:
        sys.exit(f"VERIFIED_NUMBERS has entries that are not E.164: {bad}")
    return nums


def assert_verified(number):
    """Hard stop before any call to a number not on the allowlist."""
    if number not in verified_numbers():
        sys.exit(f"REFUSED: {number} is not in VERIFIED_NUMBERS. No call placed.")
    return number


# ---------- money ----------

def rate_per_min():
    return float(setting("RATE_PER_MIN_USD", "0.06"))


def budget():
    return float(setting("BUDGET_USD", "5"))


def estimate_usd(minutes_list):
    """Telephony bills in whole minutes, so round every call up."""
    mins = sum(math.ceil(m) for m in minutes_list)
    return mins, round(mins * rate_per_min(), 2)


LEDGER = ROOT / "runs" / "ledger.jsonl"


def spent_usd():
    """Actual spend from executions we pulled. Bolna reports cost in cents."""
    if not LEDGER.exists():
        return 0.0
    total = 0.0
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        if line.strip():
            total += json.loads(line).get("cost_usd") or 0.0
    return round(total, 4)


def cost_usd(execution, wallet_before=None, wallet_after=None):
    """Wallet is in cents (485.0 = $4.85; verified: a 124 s call moved it 485 -> 470 and
    total_cost said 15). The wallet delta is the truth; total_cost is the fallback.
    cost_breakdown.total_cost_to_deduct came back negative once, so it is not used."""
    if isinstance(wallet_before, (int, float)) and isinstance(wallet_after, (int, float)):
        return round((wallet_before - wallet_after) / 100.0, 4)
    cents = execution.get("total_cost")
    return None if cents is None else round(float(cents) / 100.0, 4)


def dump(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))
