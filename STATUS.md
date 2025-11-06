# dioxide Project Status

**Last Updated**: 2025-11-06
**Current Milestone**: 0.0.2-alpha
**Latest Release**: v0.0.1-alpha (Nov 6, 2025)
**Progress**: Planning next sprint

---

## Quick Summary

🎉 **v0.0.1-alpha RELEASED** - Published to Test PyPI on Nov 6, 2025
✅ **All 6 milestone issues complete** - 100% of 0.0.1-alpha scope delivered
✅ **CI/CD working** - Full automation from tag to PyPI release
🎯 **Next up**: 0.0.2-alpha - Circular dependency detection

---

## Recent Releases

### v0.0.1-alpha (Released Nov 6, 2025) 🎉

**Published to**: Test PyPI at https://test.pypi.org/project/dioxide/

**What shipped**:
- @component decorator for auto-discovery
- Container.scan() for automatic registration
- Constructor dependency injection
- SINGLETON and FACTORY scopes
- Manual provider registration
- Type-safe Container.resolve() with mypy support
- 100% test coverage (29 tests passing)
- Full CI/CD automation
- Cross-platform wheels (Linux, macOS, Windows)

**Installation**:
```bash
pip install -i https://test.pypi.org/simple/ dioxide
```

**GitHub Release**: https://github.com/mikelane/dioxide/releases/tag/v0.0.1-alpha

---

## Current Sprint (0.0.2-alpha)

### 🎯 Sprint Goal
"Make it safe" - Add circular dependency detection with clear error messages

### 📋 Planned Work
- Issue #5: Detect and report circular dependencies

### 🔄 In Progress
- Planning and scoping 0.0.2-alpha

### ✅ Completed This Week
- Released v0.0.1-alpha to Test PyPI
- Closed 8 obsolete issues from old planning
- Created new milestone structure (0.0.2-alpha, 0.0.3-alpha, 0.1.0-beta)
- Reorganized backlog to match ROADMAP.md

---

## Milestone Progress

### 0.0.1-alpha (RELEASED ✅)
**[View milestone →](https://github.com/mikelane/dioxide/milestone/4)**

**Progress**: 100% (6 of 6 issues complete)

| Issue | Status | Completed |
|-------|--------|-----------|
| #19 Singleton Caching Bug | ✅ DONE | Oct 31, 2025 |
| #20 Manual Provider Registration | ✅ DONE | Oct 31, 2025 |
| #21 Type Safety Testing | ✅ DONE | Nov 6, 2025 |
| #22 GitHub Actions CI | ✅ DONE | Nov 3, 2025 |
| #23 GitHub Actions Release | ✅ DONE | Nov 4, 2025 |
| #24 API Documentation | ✅ DONE | Nov 6, 2025 |

### 0.0.2-alpha (PLANNED)
**[View milestone →](https://github.com/mikelane/dioxide/milestone/5)**

**Progress**: 0% (0 of 1 issues complete)

| Issue | Status | Estimated |
|-------|--------|-----------|
| #5 Circular Dependency Detection | ⏳ TODO | 1 week |

**Target**: Mid-late November 2025

---

## Critical Path to 0.0.2-alpha

What needs to happen for the next release:

1. ⏳ **Implement circular dependency detection (#5)** ← NEXT
   - Design: Use petgraph::algo::toposort for cycle detection
   - Implementation: Add cycle detection during Container.scan()
   - Testing: Add tests for direct and indirect cycles
   - Error messages: Show full cycle path in error
2. ⏳ **Test and validate** - Ensure 100% coverage maintained
3. ⏳ **Release to Test PyPI** - Tag v0.0.2-alpha

**Estimated time to release**: 1 week (per ROADMAP.md)

---

## Quality Metrics

### Test Suite
- **Tests**: 29 passing, 3 skipped (circular dependency detection out of scope)
- **Coverage**: 100% line coverage, 100% branch coverage ✅
- **Type Safety**: mypy strict mode passing ✅

### Code Quality
- Ruff formatting: ✅ Passing
- Ruff linting: ✅ Passing
- isort: ✅ Passing
- mypy: ✅ Passing
- Cargo fmt: ✅ Passing
- Cargo clippy: ✅ Passing

---

## Known Issues

### Blocking Next Release
- None currently - ready to start 0.0.2-alpha work

### Future Features (Backlog)
- #2: Inject values by parameter name
- #4: Graceful shutdown of singleton resources
- #15: Set up pytest-bdd framework

---

## Recent Commits

```
6a53a75 Add comprehensive pre-commit hooks for local development (#26)
c34f4a3 Fix CI: Add maturin to dev dependencies (#27)
463253c docs: update STATUS.md with CI/CD completion (#23)
9e4ce5f fix(release): add mypy to test dependencies (#23)
34127d0 feat: add release automation and CHANGELOG for 0.0.1-alpha (#23)
5fe2f61 fix(ci): consolidate and fix GitHub Actions workflows (#22)
40bd88b docs: add work tracking and project management guide to CLAUDE.md
c16f03e docs: update project tracking to reflect completed work
```

---

## Next Actions

**This Week** (by Nov 13):
1. Review Issue #5 requirements and design approach
2. Plan implementation strategy for circular dependency detection
3. Set up test cases for cycle detection (direct and indirect cycles)

**Next Sprint (0.0.2-alpha)**:
1. Implement circular dependency detection in Container.scan()
2. Add clear error messages showing full cycle path
3. Maintain 100% test coverage
4. Release v0.0.2-alpha to Test PyPI
5. Target: Mid-late November 2025

---

## Documentation Status

| Document | Status | Last Updated |
|----------|--------|--------------|
| STATUS.md | ✅ Current | 2025-11-04 |
| ROADMAP.md | ✅ Current | 2025-11-02 |
| 0.0.1-ALPHA_SCOPE.md | ✅ Current | 2025-11-02 |
| RELEASE_CHECKLIST.md | ✅ Current | 2025-11-02 |
| CHANGELOG.md | ✅ Current | 2025-11-04 |
| README.md | ⚠️ Needs update | - |
| CONTRIBUTING.md | ❌ Doesn't exist | - |

---

## How to Use This Document

- **Updated**: Weekly on Fridays (or after major milestones)
- **Purpose**: Single source of truth for current project status
- **Audience**: Contributors, maintainers, users
- **Format**: Markdown for GitHub display

**Note**: For long-term vision, see [ROADMAP.md](ROADMAP.md). For release details, see [docs/RELEASE_CHECKLIST_0.0.1-alpha.md](docs/RELEASE_CHECKLIST_0.0.1-alpha.md).

---

**Next Status Update**: Friday, Nov 13, 2025

---

## CI/CD Infrastructure (Completed Nov 4, 2025)

### GitHub Actions CI Pipeline ✅
- **Test Matrix**: 3 Python versions (3.11, 3.12, 3.13) × 3 OS (Ubuntu, macOS, Windows)
- **Coverage**: Codecov integration with 95% branch coverage requirement
- **Linting**: Python (ruff, mypy, isort) + Rust (clippy, fmt)
- **Runtime**: ~3 minutes per run
- **Status**: All jobs passing

### GitHub Actions Release Pipeline ✅
- **Wheel Building**: 9 platform-specific wheels + source distribution
- **Testing**: Validates wheels on all platforms before publish
- **Publishing**: Automatic to Test PyPI (alpha) or PyPI (stable)
- **GitHub Release**: Auto-generates release with changelog and artifacts
- **Cost Controls**: Timeout limits on all jobs (10-30 minutes)
- **Runtime**: ~12 minutes total (4 minutes wall time with parallelization)
- **Status**: Fully functional, tested, ready for production use

### What's Ready
1. Complete CI/CD pipeline from PR to PyPI
2. Multi-platform wheel building and testing
3. Automated release process (tag → build → test → publish → release)
4. Cost-optimized with aggressive caching and timeouts
5. CHANGELOG.md ready for 0.0.1-alpha

### What's Needed
1. PyPI token configuration (user action required)
2. Optional: API documentation for stable release
