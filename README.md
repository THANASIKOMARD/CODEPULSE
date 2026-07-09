# codepulse

**Your git history already knows which files will break next.**

codepulse reads a repository's git history and ranks files by how often they
change (churn), how complex they are, and how tightly they're coupled to the
rest of the codebase — surfacing the *hotspots* where bugs and rework cluster.

Inspired by the "hotspot" technique from Adam Tornhill's
*Your Code as a Crime Scene*. Written from scratch on raw `git log --numstat`,
with **zero runtime dependencies** (Python stdlib only).

## Quickstart

```bash
pip install -e .

python -m codepulse scan .                       # scan current repo (last 90 days)
python -m codepulse scan <path> --since 5.years  # wider window
python -m codepulse scan <path> --top 20         # show more files
python -m codepulse scan <path> --json           # machine-readable output

python -m codepulse trend <file> .               # see how one file's metrics changed across scans

python -m codepulse drift --from 3 --to 7 .      # diff two past scans by run_id
python -m codepulse drift --from 3 --to 7 --json # machine-readable diff

python -m codepulse predict .                    # forecast which files will cross the risk zone
python -m codepulse predict . --threshold 300 --within-days 14
python -m codepulse predict . --json

pip install -e ".[dashboard]"                    # extra: only needed for the dashboard below
python -m codepulse dashboard .                  # local web dashboard at http://127.0.0.1:8000
python -m codepulse dashboard . --port 9000      # use a different port
```

Every `scan` saves its results to `<repo>/.codepulse/history.db` (git-ignored,
local to the repo). Run `scan` a few times over days/weeks, then `trend`
shows how a file's score/roi moved between those runs, `drift` diffs
any two of those runs directly — files added, removed, or changed, ranked
by how much their roi moved — and `predict` fits a linear regression over
a file's roi history to forecast the date it will cross a risk threshold
(default roi ≥ 500), so you can act before a file becomes a hotspot, not after.

`dashboard` serves all of the above as a local, read-only web UI over the same
`.codepulse/history.db` — hotspot table, per-file trend chart, run-to-run drift
chart, and the decay/prediction panel in one page. It binds to `127.0.0.1`
only (no `--host` flag) and is scoped to whatever repo path you pass it, same
as every other command. Chart.js is vendored locally rather than loaded from
a CDN, so the page works fully offline once installed.

## Example

```
     ROI   Score  Chn   Cplx   Role Lnk  Au  File
----------------------------------------------------------------------------------------
  268766  144720   45   3216   core  60   6  src/flask/app.py
   58316   32260   20   1613   core  42   6  src/flask/sansio/app.py
   54167   31920   21   1520   core  23   8  src/flask/cli.py
   47510   25839   33    783   core  52   8  src/flask/helpers.py
```

`!` after the author count flags a bus-factor risk (a single contributor owns the file).

## How the score works

Every metric comes from git history or the file itself — no configuration, no magic:

| Metric | Meaning | Source |
|--------|---------|--------|
| **Churn** | how often the file changed | `git log --numstat` |
| **Complexity** | indentation depth (nesting proxy) | file contents |
| **Links** | how many files it co-changes with | co-change coupling |
| **Authors** | distinct contributors (bus factor) | commit authors |
| **Role** | core / test / docs / config | path heuristics |

The ranking is built in two steps:

```
score = churn × complexity
        └─ isolates the dangerous quadrant: files that are BOTH complex
           AND frequently changed (complex-but-stable or simple-but-churny
           code is not the problem).

roi   = score × role_weight × centrality_boost
        ├─ role_weight   core 1.0 / config 0.6 / test 0.4 / docs 0.2
        └─ centrality_boost  1.0 → ~2.0 as coupling links grow (bounded, so
                             coupling refines the ranking, never dominates it).
```

Bus-factor risk is reported as a column, deliberately kept out of the score so
the ranking stays explainable.

## Roadmap

**v0.1 — Core Engine**
- [x] Git churn analysis (`git log --numstat`, rename & binary handling)
- [x] Indentation-based complexity metric
- [x] Co-change coupling analysis
- [x] Authorship / knowledge-risk (bus factor)
- [x] File role classification (core / test / docs / config)
- [x] Hotspot score = churn × complexity
- [x] ROI ranking (role + centrality weighted)
- [x] Unified `scan` report + `--json` output
- [x] Test suite (parser, complexity, coupling, roles)

**v0.2 — Trend Tracking**
- [x] SQLite snapshot of every `scan` (`<repo>/.codepulse/history.db`)
- [x] `trend` command (per-file history across past scans)

**v0.3 — Drift Detection**
- [x] `drift` command (diff two runs by `run_id`: files added/removed/changed)
- [x] Ranked by roi impact, `--json` output

**v0.4 — Decay Prediction**
- [x] Linear regression over a file's roi history (`decay.py`)
- [x] `predict` command — forecasts the date a file crosses a risk threshold
- [x] `--threshold` / `--within-days` tuning, `--json` output

**v1.0 — Dashboard**
- [x] FastAPI backend (`/api/latest`, `/api/trend`, `/api/drift`, `/api/predict`, `/api/paths`, `/api/runs`)
- [x] Local-only web UI (`127.0.0.1`) — hotspot table, trend chart, drift chart, decay panel
- [x] Chart.js vendored locally (no CDN, no external runtime dependency)
- [x] `dashboard` command

**Next — Polish & Release**
- [ ] Validate against a real production repo (in progress)
- [ ] README demo GIF
- [ ] GitHub Release

**Ideas beyond v1.0**
- [ ] Feed hotspots into an LLM for root-cause diagnosis

## License
MIT