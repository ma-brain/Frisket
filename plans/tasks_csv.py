#!/usr/bin/env python3
"""Generate plans/TASKS.csv from plans/Working-plan.md and check task dependencies.

Usage: python3 plans/tasks_csv.py [--check]
"""
import csv, io, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLAN = HERE / "Working-plan.md"
OUT = HERE / "TASKS.csv"

def tid_key(t):
    p, n = t[1:].split(".")
    return (int(p), int(n))

def expand(dep, ids):
    dep = dep.strip()
    m = re.fullmatch(r"(T\d+\.\d+)\s*[–-]\s*(T\d+\.\d+)", dep)
    if m:
        a, b = map(tid_key, m.groups())
        return [t for t in ids if a <= tid_key(t) <= b]
    return [dep] if re.fullmatch(r"T\d+\.\d+", dep) else []

def main():
    text = PLAN.read_text(encoding="utf-8")
    phases = {m.group(1): m.group(2) for m in re.finditer(r"^## \d+\. (P\d+) — (.+)$", text, re.M)}
    rows, errors = [], []
    blocks = re.split(r"^### ", text, flags=re.M)[1:]
    ids = [b.split()[0] for b in blocks if re.match(r"T\d+\.\d+ ", b)]
    seen = set()
    for b in blocks:
        m = re.match(r"(T(\d+)\.\d+) (.+)", b)
        if not m:
            continue
        tid, ph, title = m.group(1), "P" + m.group(2), m.group(3).strip()
        if tid in seen:
            errors.append(f"{tid}: duplicate id")
        dm = re.search(r"\*\*Depends on:\*\* (.+?)\.(?: \*\*|\s*$)", b, re.M)
        deps_raw = dm.group(1) if dm else ""
        deps = [] if deps_raw.strip() == "none" else [x for d in deps_raw.split(",") for x in expand(d, ids)]
        for d in deps:
            if d not in ids:
                errors.append(f"{tid}: unknown dependency {d}")
            elif tid_key(d) >= tid_key(tid):
                errors.append(f"{tid}: depends on later task {d}")
        sm = re.search(r"\*\*Spec:\*\* (.+?)\.(?: \*\*|\s*$)", b, re.M)
        rows.append([tid, ph, phases.get(ph, ""), title, "; ".join(deps) or "none", sm.group(1) if sm else ""])
        seen.add(tid)
    for u in re.findall(r"`ui/([\w.-]+\.png)`", text):
        if not (HERE.parent / "ui" / u).exists():
            errors.append(f"missing mockup ui/{u}")
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["id", "phase", "phase_title", "title", "depends_on", "spec_refs"])
    w.writerows(rows)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        sys.exit(1)
    if "--check" in sys.argv:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != buf.getvalue():
            print("TASKS.csv is stale", file=sys.stderr)
            sys.exit(1)
    else:
        OUT.write_text(buf.getvalue(), encoding="utf-8")
    print(f"{len(rows)} tasks OK")

if __name__ == "__main__":
    main()
