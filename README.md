# codepulse

**Your git history already knows which files will break next.**

codepulse reads a repository's git history and ranks files by how often they
change (churn), how complex they are, and how tightly they're coupled to the
rest of the codebase — surfacing the *hotspots* where bugs and rework cluster.

Inspired by the "hotspot" technique from Adam Tornhill's
*Your Code as a Crime Scene*. The churn engine is written from scratch on raw
`git log --numstat` to understand exactly what git records.

## Quickstart
pip install -e .
python -m codepulse scan .            # scan current repo
python -m codepulse scan . --top 20   # show more files
​

## Roadmap
- [x] Project scaffold + CLI skeleton
- [x] Git churn analysis (90-day window)
- [x] `scan` command: top-churn table
- [x] Repo root detection + graceful non-repo handling
- [x] Per-commit file grouping (coupling groundwork)
- [x] Handle renames & binary files in numstat
- [ ] Complexity metric (lines / cyclomatic)
- [ ] Co-change coupling analysis
- [ ] Hotspot score = churn × complexity
- [ ] Bus-factor / knowledge risk

## License
MIT