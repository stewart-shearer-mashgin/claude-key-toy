#!/usr/bin/env python3
"""
keydemo - a toy of the per-user CI-token idea.

Strips the real thing (Vault/age/GitHub secrets/Claude) down to its two ideas:
  1. ENROLL: a user registers their token under their login, with an expiry.
  2. RESOLVE: CI picks the PR author's token; if it's missing or EXPIRED,
     it falls back to a shared token.

Store is just a JSON file. Tokens are fake. Expiry is in seconds so you can
watch it lapse in real time.

  ./keydemo.py enroll alice --ttl 15
  ./keydemo.py resolve alice
  ./keydemo.py list
  ./keydemo.py reset
"""
import argparse, json, os, sys, time

STORE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "store.json")
SHARED = "tok-SHARED-org-fallback"


def load():
    if not os.path.exists(STORE):
        return {"keys": {}}
    return json.load(open(STORE))


def save(d):
    json.dump(d, open(STORE, "w"), indent=2)


def enroll(login, ttl, token):
    d = load()
    token = token or f"tok-{login}-{int(time.time())%100000}"
    d["keys"][login] = {"token": token, "expires": time.time() + ttl}
    save(d)
    print(f"enrolled '{login}'  token={token}  ttl={ttl}s")


def resolve(login, quiet=False):
    d = load()
    entry = d["keys"].get(login)
    now = time.time()
    if entry and entry["expires"] > now:
        left = int(entry["expires"] - now)
        if not quiet:
            print(f"[{login}] -> per-user key {entry['token']}  (expires in {left}s)")
        return entry["token"], "per-user"
    reason = "EXPIRED" if entry else "not enrolled"
    if not quiet:
        ago = f" ({int(now - entry['expires'])}s ago)" if entry else ""
        print(f"[{login}] -> {reason}{ago}, falling back to shared: {SHARED}")
    return SHARED, "fallback"


def list_(_):
    d = load()
    now = time.time()
    if not d["keys"]:
        print("(nobody enrolled)")
        return
    for login, e in d["keys"].items():
        left = int(e["expires"] - now)
        state = f"valid, {left}s left" if left > 0 else f"EXPIRED {-left}s ago"
        print(f"  {login:24} {e['token']:28} {state}")


def reset(_):
    if os.path.exists(STORE):
        os.remove(STORE)
    print("store cleared")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("enroll"); e.add_argument("login"); e.add_argument("--ttl", type=int, default=15); e.add_argument("--token", default="")
    r = sub.add_parser("resolve"); r.add_argument("login")
    sub.add_parser("list"); sub.add_parser("reset")
    a = p.parse_args()
    if a.cmd == "enroll":  enroll(a.login, a.ttl, a.token)
    elif a.cmd == "resolve": resolve(a.login)
    elif a.cmd == "list":  list_(a)
    elif a.cmd == "reset": reset(a)


if __name__ == "__main__":
    main()
