"""Step 4: score every pulled call on the LOCKED rubric (rubric.json).

rubric/rubric.json is hash-locked in rubric/rubric.lock. If it changes,
this script refuses to run, so v1 and v2 are always scored on the same checks.

Automatic checks (C01-C07) come from the transcript and Bolna's interruption stats.
Manual checks (C08-C12) are read from runs/review.json. Each needs a verdict (true/false/"na")
plus a transcript quote as evidence; until then it is "unscored".

    python 04_score.py            # score what is in runs/
    python 04_score.py --refresh  # re-pull every execution from Bolna first (free, read-only)
"""
import difflib
import hashlib
import re
import sys
from pathlib import Path
from bolna import dump, get, load

ROOT = Path(__file__).resolve().parent.parent  # repo root

LOCK = ROOT / "rubric" / "rubric.lock"
LOCKED_FILES = ["rubric/rubric.json"]


def digest(name):
    return hashlib.sha256((ROOT / name).read_bytes()).hexdigest()


def check_lock():
    if not LOCK.exists():
        sys.exit("rubric.lock missing. The rubric must be locked before scoring.")
    lock = load(LOCK)
    for f in LOCKED_FILES:
        if lock.get(f) != digest(f):
            sys.exit(f"REFUSED: {f} changed after the rubric was locked. Scores would not be comparable.")


RUBRIC = load(ROOT / "rubric" / "rubric.json")
RS_PAT = re.compile(r"(?<![A-Za-z])R[sS]\.?(?![A-Za-z])|\bINR\b|₹|\d\s*/-")
RUPEE_WORDS = re.compile(r"rupees?|rupaye|rupaiye|rupay[ie]|rupaa?yi|रुपये|रुपए|रुपया|ರೂಪಾಯಿ", re.I)
DIGIT_WORDS = {
    "zero": "0", "oh": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9",
    "shoonya": "0", "shunya": "0", "ek": "1", "do": "2", "teen": "3", "char": "4", "chaar": "4",
    "paanch": "5", "panch": "5", "chhah": "6", "chhe": "6", "saat": "7", "aath": "8", "nau": "9",
    "sonne": "0", "ondu": "1", "eradu": "2", "mooru": "3", "naalku": "4", "aidu": "5",
    "aaru": "6", "elu": "7", "entu": "8", "ombattu": "9",
}


def parse(transcript):
    turns = []
    for line in (transcript or "").splitlines():
        m = re.match(r"^\s*(assistant|user)\s*:\s*(.*)$", line, re.I)
        if m:
            turns.append([m.group(1).lower(), m.group(2)])
        elif turns:
            turns[-1][1] += " " + line
    return turns


def separated_digits(text):
    """Longest run of digits spoken one at a time (single digits or digit words)."""
    toks = re.findall(r"[A-Za-z]+|\d+", text.lower())
    best, run = "", ""
    for t in toks:
        d = t if (t.isdigit() and len(t) == 1) else DIGIT_WORDS.get(t)
        if d is not None:
            run += d
            best = max(best, run, key=len)
        elif t in {"and", "then", "comma"}:
            continue
        else:
            run = ""
    return best


def caller_number(turns):
    """Last full 10-digit number the caller said (digits, grouped digits or digit words)."""
    found = None
    for r, t in turns:
        if r != "user":
            continue
        joined = re.sub(r"(?<=\d)[\s-]+(?=\d)", "", t)
        for m in re.findall(r"(?<!\d)(\d{10})(?!\d)", joined):
            found = m
        w = separated_digits(t)
        if len(w) >= 10:
            found = w[-10:]
    return found


def mask(n):
    return f"******{n[-4:]}" if n else "none"


def auto_check(key, turns, stats, scenario_id):
    agent_turns = [t for r, t in turns if r == "assistant"]
    agent = " ".join(agent_turns)
    low = agent.lower()
    if key == "no_rs":
        hits = [t for t in agent_turns if RS_PAT.search(t)]
        return (True, "none") if not hits else (False, f"found in: \"{hits[0][:120]}\"")
    if key == "says_rupees":
        # a price = a number next to Rs/rupees, or a menu price not followed by "min" (so "35-40 minutes" is not a price)
        menu_prices = {"199", "349", "499", "249", "429", "599", "279", "459", "649", "299", "699",
                       "60", "120", "30", "40", "129", "99"}
        nums = [m for m in re.finditer(r"(?<!\d)(\d{2,4})(?!\d)", agent)
                if not re.match(r"\s*-?\s*(\d+\s*)?min", agent[m.end():m.end() + 12], re.I)]
        priced = RS_PAT.search(agent) or RUPEE_WORDS.search(agent) or any(m.group(1) in menu_prices for m in nums)
        if not priced:
            return "na", "agent spoke no price"
        ok = bool(RUPEE_WORDS.search(agent))
        return ok, "says rupees" if ok else "prices spoken without the word rupees"
    if key == "readback_breakdown":
        if not re.search(r"(?<!sub)total", low):
            return "na", "no order read back"
        parts = {"subtotal": "subtotal" in low, "delivery": "delivery" in low,
                 "total": re.search(r"(?<!sub)total", low) is not None}
        ok = all(parts.values())
        return ok, "has " + ", ".join(k for k, v in parts.items() if v) + (
            "" if ok else "; missing " + ", ".join(k for k, v in parts.items() if not v))
    if key == "phone_readback":
        want = caller_number(turns)
        if not want:
            return "na", "caller gave no 10-digit number"
        runs = [separated_digits(t) for t in agent_turns]
        ok = any(want in r for r in runs)
        longest = max(runs, key=len, default="")
        return ok, (f"read back {mask(want)} digit by digit" if ok else
                    f"no digit-by-digit read-back of {mask(want)} (longest digit run {len(longest)})")
    if key == "no_repeat_question":
        qs = [t.strip().lower() for t in agent_turns if "?" in t]
        for i in range(len(qs)):
            for j in range(i + 1, len(qs)):
                if difflib.SequenceMatcher(None, qs[i], qs[j]).ratio() >= 0.8:
                    return False, f"asked twice: \"{qs[j][:100]}\""
        return True, f"{len(qs)} questions, none repeated"
    if key == "no_premature_reply":
        if scenario_id == "08-interrupting":
            return "na", "caller interrupts on purpose in this script"
        n = stats.get("user_interrupted_agent_count")
        if n is None:
            return "na", "Bolna gave no interruption stats"
        return n <= 1, f"agent jumped in and got talked over {n} time(s)"
    if key == "never_talks_over":
        n = stats.get("agent_interrupted_user_count")
        if n is None:
            return "na", "Bolna gave no interruption stats"
        return n == 0, f"agent talked over the caller {n} time(s)"
    raise KeyError(key)


def main():
    check_lock()
    refresh = "--refresh" in sys.argv
    review_path = ROOT / "runs" / "review.json"
    review = load(review_path) if review_path.exists() else {}
    scores = {}
    for vdir in sorted((ROOT / "runs").glob("v*")):
        for f in sorted(vdir.glob("*.json")):
            run = load(f)
            if refresh:
                run["execution"] = get(f"/executions/{run['execution_id']}")
                dump(f, run)
            ex = run["execution"]
            if ex.get("status") != "completed" or not ex.get("conversation_duration"):
                continue  # never connected: nothing to score
            key = f"{run['version']}/{run['scenario']}"
            turns = parse(ex.get("transcript"))
            lat = ex.get("latency_data") or {}
            stats = lat.get("interruption_stats") or {}
            rv = review.setdefault(key, {})
            results = {}
            for c in RUBRIC["checks"]:
                if c["type"] == "auto":
                    v, why = auto_check(c["key"], turns, stats, run["scenario"])
                else:
                    item = rv.setdefault(c["key"], {"verdict": None, "evidence": ""})
                    v = item["verdict"] if item.get("evidence") else None
                    why = item.get("evidence") or "unscored: needs a verdict with a transcript quote"
                results[c["id"]] = {"key": c["key"], "result": v, "evidence": why}
            scores[key] = {
                "status": ex.get("status"),
                "duration_s": ex.get("conversation_duration"),
                "time_to_first_audio_ms": lat.get("time_to_first_audio"),
                "caller_cut_agent_off": stats.get("user_interrupted_agent_count"),
                "agent_talked_over_caller": stats.get("agent_interrupted_user_count"),
                "cost_cents": ex.get("total_cost"),
                "checks": results,
                "extracted_data": ex.get("extracted_data"),
            }
            mark = {True: "P", False: "F", "na": "-", None: "?"}
            print(f"{key:34s} " + " ".join(f"{cid}={mark[r['result']]}" for cid, r in results.items()))
    # drop review keys that are not rubric checks, so nothing outside the rubric is ever counted
    valid = {c["key"] for c in RUBRIC["checks"] if c["type"] == "manual"}
    for k in review:
        review[k] = {ck: cv for ck, cv in review[k].items() if ck in valid}
    dump(ROOT / "runs" / "scores.json", scores)
    dump(review_path, review)
    todo = sum(1 for s in scores.values() for r in s["checks"].values() if r["result"] is None)
    print(f"\nRubric {RUBRIC['version']}: {len(RUBRIC['checks'])} checks. Wrote runs/scores.json. "
          f"{todo} manual check(s) unscored. Legend: P pass, F fail, - n/a, ? unscored.")


if __name__ == "__main__":
    main()
