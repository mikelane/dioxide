# dioxide Project Status

**Last Updated**: 2025-11-08
**Current Milestone**: 0.0.2-alpha (MLP Realignment)
**Latest Release**: v0.0.1-alpha (Nov 6, 2025)
**Progress**: MLP realignment sprint kicked off - 8 new issues created

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
- Issue #65: [MLP] Implement @component decorator (singleton + factory scopes)
- Issue #66: [MLP] Implement @component.implements(Protocol)
- Issue #67: [MLP] Implement Initializable and Disposable lifecycle protocols
- Issue #68: [MLP] Implement @profile decorator system (CORE - cornerstone feature)
- Issue #69: [MLP] Update container.scan() to accept package and profile parameters
- Issue #70: [MLP] Create global singleton container pattern
- Issue #71: [MLP] Add container[Type] resolution syntax (nice-to-have)
- Issue #72: [MLP] Create complete notification service example application
- Issue #73: [MLP] Add FastAPI integration example
- Issue #74: [DOCS] Create migration guide from v0.0.1-alpha to v0.0.2-alpha
- Issue #75: [DOCS] Rewrite documentation with MLP syntax

### 🔄 In Progress
- MLP realignment sprint initiated (Nov 8, 2025)
- 11 GitHub issues created for complete MLP alignment
- Next up: Start implementing core API changes (#65, #66, #68)

### ✅ Completed This Week (Nov 3-8, 2025)
- Released v0.0.1-alpha to Test PyPI
- Created MLP_VISION.md (canonical design document)
- Completed PM assessment (DX_EVALUATION.md)
- Created document audit (docs/DOCUMENT_AUDIT.md)
- Deleted historical documents (0.0.1-alpha scope, checklists)
- **✅ Created 11 comprehensive GitHub issues for MLP realignment**:
  - #65-#67: Core API updates (@component, .implements(), lifecycle)
  - #68-#70: Profile system and container updates (CRITICAL)
  - #71: Nice-to-have container[Type] syntax
  - #72-#73: Example applications (notification service, FastAPI)
  - #74-#75: Migration guide and documentation rewrite
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
**[View milestone →](https://github.com/mikelane/dioxide/milestone/4)**

**Progress**: 0% (0 of 11 issues complete)

#### Phase 1: Core API Realignment (Weeks 1-3)
| Issue | Status | Estimated |
|-------|--------|-----------|
| #65 @component decorator (singleton + factory) | ⏳ TODO | 2 days |
| #66 @component.implements(Protocol) | ⏳ TODO | 2 days |
| #68 @profile decorator system | ⏳ TODO | 3 days |
| #69 container.scan() with package & profile | ⏳ TODO | 2 days |
| #70 Global singleton container | ⏳ TODO | 1 day |

#### Phase 2: Lifecycle Management (Weeks 4-5)
| Issue | Status | Estimated |
|-------|--------|-----------|
| #67 Initializable and Disposable protocols | ⏳ TODO | 3 days |

#### Phase 3: Examples & Documentation (Week 6)
| Issue | Status | Estimated |
|-------|--------|-----------|
| #72 Notification service example | ⏳ TODO | 2 days |
| #73 FastAPI integration example | ⏳ TODO | 1 day |
| #74 Migration guide (v0.0.1 → v0.0.2) | ⏳ TODO | 1 day |
| #75 Documentation rewrite with MLP syntax | ⏳ TODO | 2 days |

#### Nice-to-Have
| Issue | Status | Estimated |
|-------|--------|-----------|
| #71 container[Type] syntax | ⏳ TODO | 1 day |

**Target**: Mid-December 2025 (6-7 weeks)
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

**This Week** (by Nov 15):
1. ✅ Complete PM assessment (DX_EVALUATION.md)
2. ✅ Create 11 comprehensive GitHub issues for MLP realignment (#65-#75)
3. ✅ Delete historical documents
4. ✅ Update Priority 0 documentation to MLP syntax (ROADMAP, README, DX_VISION)
5. ⏳ Move Issue #5 (circular dependencies) to 0.0.4-alpha milestone
6. ⏳ Start Phase 1: Core API changes (#65, #66, #68, #69, #70)

**Next 3 Weeks (Phase 1 - Core API Realignment)**:
1. Implement @component decorator improvements (#65)
2. Implement @component.implements(Protocol) (#66)
3. Implement @profile decorator system (#68) - CRITICAL
4. Update container.scan() with package & profile (#69)
5. Create global singleton container (#70)
6. Maintain 100% test coverage throughout
7. Target: Late November 2025

**Weeks 4-5 (Phase 2 - Lifecycle Management)**:
1. Implement Initializable and Disposable protocols (#67)
2. Add async context manager support
3. Update examples

**Week 6 (Phase 3 - Examples & Docs)**:
1. Create notification service example (#72)
2. Create FastAPI integration example (#73)
3. Write migration guide (#74)
4. Rewrite all documentation (#75)
5. Release v0.0.2-alpha to Test PyPI

**Future Milestones**:
- 0.0.3-alpha: Polish and circular dependency detection (#5)
- 0.0.4-alpha: Beta preparation
- 0.1.0-beta: MLP complete, API freeze (mid-December 2025)

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

**Next Status Update**: Friday, Nov 15, 2025 (Phase 1 progress report)

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
