# dioxide Project Status

**Last Updated**: 2025-11-28
**Current Milestone**: Documentation Modernization
**Latest Release**: v0.1.0-beta.2 (Nov 23, 2025)
**Status**: MLP Complete - Documentation polish in progress

---

## Quick Summary

**v0.1.0-beta.2 RELEASED** - MLP Complete, production-ready
**Documentation Modernization**: 7 of 17 issues complete (41%)
**This Week**: README positioning, Sphinx extensions, RTD config, Furo theme, Markdown index

---

## Recent Releases

### v0.1.0-beta.2 (Released Nov 23, 2025)

**Published to**: PyPI at https://pypi.org/project/dioxide/

**What shipped**:
- MLP Complete - All must-have features implemented
- Hexagonal architecture API (`@adapter.for_()`, `@service`, `Profile`)
- Lifecycle management (`@lifecycle`, `async with container`)
- Circular dependency detection at scan time
- Performance benchmarking (all targets exceeded)
- FastAPI integration example
- Comprehensive testing guide (fakes > mocks philosophy)
- Release process improvements (Test PyPI staging, wheel validation)

**Installation**:
```bash
pip install dioxide
```

---

## Current Sprint: Documentation Modernization

### Sprint Goal
**"Documentation Excellence"** - Modern, beautiful, user-friendly documentation

### Completed This Week (Nov 28, 2025)

| PR | Issues | Description |
|----|--------|-------------|
| #186 | #185 | Migration guide from dependency-injector |
| #188 | #187 | Honest benchmark comparison vs dependency-injector |
| #221 | #206 | ReadTheDocs config modernization (uv, jobs pattern) |
| #224 | #205, #208 | Furo theme with autoapi_root fix |
| #223 | #207 | Convert index.rst to MyST Markdown |
| #225 | #189 | README honest performance positioning |
| #226 | #209, #210, #211 | Sphinx extensions (copybutton, design, mermaid) |

### Remaining Work

**Phase 3 - Developer Experience**:
- #213: sphinx-autobuild for live reload
- #214: linkcheck in CI workflow

**Phase 4 - Content Excellence**:
- #217: Visual landing page with hero section
- #218: Architecture diagrams for hexagonal patterns
- #219: Cookbook section with real-world recipes
- #220: "Why dioxide?" comparison page

**Phase 5 - Polish**:
- #215: sphinx-tippy for hover tooltips
- #216: sphinx-togglebutton for collapsible sections
- #212: Migrate to PEP 735 dependency-groups

---

## Milestone Progress

| Milestone | Open | Closed | Status |
|-----------|------|--------|--------|
| 0.1.0-beta | 0 | 6 | COMPLETE |
| Documentation Modernization | 10 | 7 | Active |
| Release Process Improvements | 1 | 6 | Nearly complete (#54 remaining) |
| Request Scoping | 4 | 3 | Post-MLP (Q1 2026) |
| Backlog | 4 | 14 | Deferred |

---

## Quality Metrics

### Test Suite
- **Tests**: 92+ passing
- **Coverage**: 100% line coverage, 100% branch coverage
- **Type Safety**: mypy strict mode passing

### CI/CD
- **Build**: Passing on all platforms (Linux, macOS, Windows)
- **Python Versions**: 3.11, 3.12, 3.13, 3.14
- **Release Automation**: Semantic versioning, Test PyPI staging, PyPI publishing

---

## Recent Commits (main)

```
d5b4db6 docs: add sphinx-copybutton, sphinx-design, and mermaid extensions (#226)
c8125c2 docs: update README with honest performance positioning (#225)
acf5653 docs: convert index.rst to MyST Markdown (#207) (#223)
00b755e docs: switch to Furo theme with autoapi_root (#205, #208) (#224)
4e4f0e9 docs: modernize ReadTheDocs configuration (#206) (#221)
ee2cf91 perf: add honest benchmark comparison vs dependency-injector (#188)
1603c04 docs: add migration guide from dependency-injector (#186)
```

---

## Next Actions

**Immediate**:
1. Continue Documentation Modernization Phase 3-4
2. Close Release Process Improvements milestone (#54)

**This Week**:
- #213: sphinx-autobuild
- #214: linkcheck CI
- #217: Landing page

**Post-MLP (Q1 2026)**:
- Request Scoping epic (#181-184)
- Backlog items

---

## Documentation

| Document | Status | Last Updated |
|----------|--------|--------------|
| STATUS.md | Current | 2025-11-28 |
| README.md | Current | 2025-11-28 |
| MLP_VISION.md | Canonical | 2025-11-07 |
| ROADMAP.md | Current | 2025-11-23 |

---

**Next Status Update**: Friday, Dec 6, 2025
