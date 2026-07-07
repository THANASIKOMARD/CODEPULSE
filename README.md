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
```

Every `scan` saves its results to `<repo>/.codepulse/history.db` (git-ignored,
local to the repo). Run `scan` a few times over days/weeks, then `trend`
shows how a file's score/roi moved between those runs.

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

**Next**
- [ ] Drift detection (compare two points in history)
- [ ] Feed hotspots into an LLM for root-cause diagnosis

## License
MIT