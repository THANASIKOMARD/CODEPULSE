# codepulse

**Your git history already knows which files will break next.**

codepulse reads a repository's git history and ranks files by how often they
change (churn), how complex they are, and how tightly they're coupled to the
rest of the codebase — surfacing the *hotspots* where bugs and rework cluster.

Inspired by [Vitals](https://github.com/chopratejas/vitals) and Adam Tornhill's
*Your Code as a Crime Scene*. Built from scratch to understand the internals.

## Quickstart
pip install -e .
python -m codepulse scan .            # scan current repo
python -m codepulse scan . --top 20   # show more files
​

## Roadmap
- [x] Project scaffold + CLI skeleton
- [ ] Git churn analysis (90-day window)
- [ ] `scan` command: top-churn table
- [ ] Repo root detection + graceful non-repo handling
- [ ] Per-commit file grouping (coupling groundwork)
- [ ] Handle renames & binary files in numstat
- [ ] Complexity metric (lines / cyclomatic)
- [ ] Co-change coupling analysis
- [ ] Hotspot score = churn × complexity
- [ ] Bus-factor / knowledge risk

## License
MIT