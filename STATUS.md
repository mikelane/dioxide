# dioxide Project Status

**Last Updated**: 2025-11-07
**Current Milestone**: 0.0.2-alpha (MLP Realignment)
**Latest Release**: v0.0.1-alpha (Nov 6, 2025)
**Progress**: Sprint planning - MLP Vision alignment

---

## Quick Summary

🎉 **v0.0.1-alpha RELEASED** - Published to Test PyPI on Nov 6, 2025
✅ **All 6 milestone issues complete** - 100% of 0.0.1-alpha scope delivered
✅ **CI/CD working** - Full automation from tag to PyPI release
🎯 **STRATEGIC SHIFT**: 0.0.2-alpha - **MLP Vision API Realignment**
⚠️ **Breaking Changes**: API will change significantly to align with MLP_VISION.md

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

## Current Sprint (0.0.2-alpha) - MLP Realignment

### 🎯 Sprint Goal
**"Align with MLP Vision"** - Realign API with canonical MLP_VISION.md specification

**Why the change?**
- v0.0.1-alpha was built before MLP Vision document existed
- Current API doesn't match MLP specification (wrong syntax, missing features)
- We're in alpha - perfect time for breaking changes
- Zero external users on Test PyPI - minimal disruption

### 📋 Planned Work (Breaking Changes)
- Issue #28: Implement `@component.factory` and `@component.implements()` syntax
- Issue #29: Implement `@profile` decorator system (core MLP feature)
- Issue #30: Update `container.scan()` to accept package and profile parameters
- Issue #31: Create global singleton container pattern
- Issue #32: Realign all documentation with MLP Vision
- Issue #33: Add `container[Type]` syntax (optional nice-to-have)

### 🔄 In Progress
- Documentation realignment (Priority 0 complete, Priority 1 remaining)
- Next up: Update CLAUDE.md with MLP syntax (Priority 1)

### ✅ Completed This Week
- Released v0.0.1-alpha to Test PyPI
- Created MLP_VISION.md (canonical design document)
- Completed PM assessment (DX_EVALUATION.md)
- Created document audit (docs/DOCUMENT_AUDIT.md)
- Deleted historical documents (0.0.1-alpha scope, checklists)
- Created 6 GitHub issues for MLP realignment (#28-#33)
- **✅ Completed Priority 0 documentation alignment**:
  - Updated DX_VISION.md to align with MLP (marked sections as post-MLP)
  - Completely rewrote ROADMAP.md v2.0.0 with MLP phase structure
  - Updated README.md with MLP syntax (Quick Start, Vision, Features)

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

### 0.0.2-alpha (IN PROGRESS - MLP Realignment)
**[View milestone →](https://github.com/mikelane/dioxide/milestone/5)**

**Progress**: 0% (0 of 6 issues complete)

| Issue | Status | Estimated |
|-------|--------|-----------|
| #28 @component.factory and .implements() syntax | ⏳ TODO | 3 days |
| #29 @profile decorator system | ⏳ TODO | 4 days |
| #30 container.scan() with package & profile | ⏳ TODO | 2 days |
| #31 Global singleton container | ⏳ TODO | 1 day |
| #32 Documentation realignment | ⏳ TODO | 2 days |
| #33 container[Type] syntax (optional) | ⏳ TODO | 1 day |

**Target**: Mid-late November 2025
**Breaking Changes**: YES (acceptable in alpha)

---

## Critical Path to 0.0.2-alpha (MLP Realignment)

What needs to happen for the next release:

1. ⏳ **Core API Changes** (Week 1-2)
   - Implement `@component.factory` syntax
   - Implement `@component.implements(Protocol)`
   - Implement `@profile` decorator system (hybrid approach)
   - Add package and profile parameters to `container.scan()`
   - Create global singleton container pattern

2. ⏳ **Documentation Realignment** (Week 2)
   - Update README with MLP syntax
   - Rewrite ROADMAP for MLP phases
   - Update all code examples
   - Add migration guide from 0.0.1 to 0.0.2

3. ⏳ **Test and Validate** (Ongoing)
   - Maintain 100% test coverage
   - Update all tests to MLP syntax
   - Type safety validation with mypy

4. ⏳ **Release to Test PyPI** - Tag v0.0.2-alpha

**Estimated time to release**: 2-3 weeks
**Why longer?** API realignment is significant work, but sets correct foundation

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
1. ✅ Complete PM assessment (DX_EVALUATION.md)
2. ✅ Create GitHub issues for MLP realignment (#28-#33)
3. ✅ Delete historical documents
4. ✅ Update Priority 0 documentation to MLP syntax (ROADMAP, README, DX_VISION)
5. ⏳ Update CLAUDE.md with MLP syntax (Priority 1)
6. ⏳ Start implementing `@component.factory` syntax (#28)

**Next Sprint (0.0.2-alpha - Weeks 1-2)**:
1. Implement all core API changes (#28-#31)
2. Realign all documentation (#32)
3. Maintain 100% test coverage throughout
4. Add migration guide from 0.0.1 to 0.0.2
5. Release v0.0.2-alpha to Test PyPI
6. Target: Mid-late November 2025

**Future Sprints** (Post-0.0.2):
- 0.0.3-alpha: Lifecycle management (`Initializable`, `Disposable`, async context manager)
- 0.0.4-alpha: Complete example + polish + circular dependency detection
- 0.1.0-beta: MLP complete, API freeze

---

## Documentation Status

| Document | Status | Last Updated |
|----------|--------|--------------|
| STATUS.md | ✅ Updated for MLP | 2025-11-07 |
| MLP_VISION.md | ✅ Canonical | 2025-11-07 |
| DX_EVALUATION.md | ✅ Current | 2025-11-07 |
| DOCUMENT_AUDIT.md | ✅ Current | 2025-11-07 |
| ROADMAP.md | ✅ Rewritten v2.0.0 | 2025-11-07 |
| README.md | ✅ Updated MLP syntax | 2025-11-07 |
| DX_VISION.md | ✅ Aligned with MLP | 2025-11-07 |
| CLAUDE.md | ⚠️ Needs update | Shows pre-MLP examples |
| CHANGELOG.md | ✅ Current | 2025-11-04 |
| 0.0.1-ALPHA_SCOPE.md | ❌ Deleted | Historical |
| RELEASE_CHECKLIST_0.0.1-alpha.md | ❌ Deleted | Historical |

---

## How to Use This Document

- **Updated**: Weekly on Fridays (or after major milestones)
- **Purpose**: Single source of truth for current project status
- **Audience**: Contributors, maintainers, users
- **Format**: Markdown for GitHub display

**Note**: For design specification, see [MLP_VISION.md](docs/MLP_VISION.md) (canonical). For PM assessment, see [DX_EVALUATION.md](DX_EVALUATION.md).

---

**Next Status Update**: Friday, Nov 15, 2025 (post API realignment progress)

---

## MLP Realignment Context

**Why are we doing this?**

dioxide v0.0.1-alpha was implemented before the MLP_VISION.md document was created. After creating the canonical MLP specification, we discovered significant API misalignment:

- **Current API**: `@component(scope=Scope.FACTORY)`, `container = Container()`, `container.scan()`
- **MLP API**: `@component.factory`, `from dioxide import container`, `container.scan("app", profile="test")`
- **Missing**: Profile system (core MLP feature), lifecycle protocols, `@component.implements()`

**Grade**: Current state is B- (75/100) - Only 36% complete toward MLP vision

**Decision**: Realign NOW while we're in alpha with zero external users. The longer we wait, the more expensive the migration becomes.

**Timeline**: 2-3 weeks for API realignment, then 1-2 weeks for lifecycle, then 1 week for polish = 4-6 weeks to MLP complete (0.1.0-beta)

For full assessment, see [DX_EVALUATION.md](DX_EVALUATION.md).

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
