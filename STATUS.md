# dioxide Project Status

**Last Updated**: 2025-11-23
**Current Milestone**: 0.1.0-beta (MLP Complete - Production Ready)
**Latest Release**: v0.0.4-alpha.1 (Nov 23, 2025)
**Progress**: v0.0.4-alpha COMPLETE! Lifecycle management and circular dependency detection fully implemented ✅

---

## Quick Summary

🎉 **v0.0.4-alpha.1 RELEASED** - Lifecycle management complete!
✅ **3 of 3 milestone issues complete** - 100% of 0.0.4-alpha scope delivered
✅ **New features** - `@lifecycle` decorator, `async with container`, circular dependency detection
✅ **MLP Progress** - 11 of 14 features complete (79%) - Grade: A+ (95/100)
🎯 **NEXT**: 0.1.0-beta - MLP Complete (Performance, FastAPI integration, testing guide)

---

## Recent Releases

### v0.0.4-alpha.1 (Released Nov 23, 2025) 🎉

**Published to**: PyPI at https://pypi.org/project/dioxide/

**What shipped**:
- `@lifecycle` decorator for opt-in lifecycle management (#67)
- `async with container:` context manager support (#95)
- `container.start()` / `container.stop()` methods (#95)
- Dependency-ordered initialization (Kahn's algorithm) (#95)
- Circular dependency detection (#5)
- Package scanning for `container.scan()` (#86)
- Function injection documentation and examples (#64)
- 100% test coverage maintained (92 tests passing)

**Installation**:
```bash
pip install dioxide==0.0.4a1
```

**GitHub Release**: https://github.com/mikelane/dioxide/releases/tag/v0.0.4-alpha.1

---

### v0.0.1-alpha (Released Nov 6, 2025)

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

## Recently Completed Sprint (0.0.4-alpha) ✅

### 🎯 Sprint Goal: "Production-Ready Resource Management"
**Status**: ✅ COMPLETE (100% - 3 of 3 issues closed)
**Completed**: Nov 23, 2025

### ✅ Completed Work (Nov 18-23, 2025)

**Epic #95: Lifecycle Management & Resource Cleanup**
- ✅ #67: `@lifecycle` decorator for opt-in lifecycle management
- ✅ #95: Container lifecycle runtime support (start/stop, async context manager)
- ✅ #5: Circular dependency detection (fail fast at startup)

**Merged Pull Requests (6 PRs)**:
- ✅ [PR #126](https://github.com/mikelane/dioxide/pull/126): Package scanning implementation (#86)
- ✅ [PR #125](https://github.com/mikelane/dioxide/pull/125): Container lifecycle runtime support (#95)
- ✅ [PR #124](https://github.com/mikelane/dioxide/pull/124): Function injection documentation (#64)
- ✅ [PR #123](https://github.com/mikelane/dioxide/pull/123): Lifecycle runtime restoration (#67)
- ✅ [PR #122](https://github.com/mikelane/dioxide/pull/122): Lifecycle type stubs (#67)
- ✅ [PR #121](https://github.com/mikelane/dioxide/pull/121): Lifecycle decorator implementation (#67)

**Deliverables**:
- ✅ `@lifecycle` decorator with `initialize()` and `dispose()` methods
- ✅ Dependency-ordered initialization using Kahn's algorithm
- ✅ Async context manager support (`async with container:`)
- ✅ Manual control methods (`container.start()`, `container.stop()`)
- ✅ Circular dependency detection at scan time
- ✅ Package scanning for `container.scan()`
- ✅ Function injection examples in README
- ✅ 100% test coverage maintained (92 tests passing)
- ✅ Released to PyPI as v0.0.4-alpha.1

---

## Previously Completed Sprint (0.0.2-alpha) ✅

### 🎯 Sprint Goal: "Hexagonal Architecture API"
**Status**: ✅ COMPLETE (100% - 11 of 11 issues closed)
**Completed**: Nov 16, 2025

### ✅ Completed Work (Nov 11-16, 2025)

**Epic #96: Hexagonal Architecture Implementation**
- ✅ #93: `Profile` enum (PRODUCTION, TEST, DEVELOPMENT, ALL)
- ✅ #94: `@adapter.for_(Port, profile=...)` decorator
- ✅ #95: `@service` decorator for core domain logic
- ✅ #97: Container profile support (`Profile` enum integration)
- ✅ #98: Port-based resolution (`container.resolve(EmailPort)`)
- ✅ #99: End-to-end hexagonal integration tests
- ✅ #100: Documentation updates with hexagonal examples
- ✅ #101: MIGRATION.md guide (v0.0.1 → v0.0.2)
- ✅ #102: Deprecation warnings for `@component` API
- ✅ #109: Complete integration test suite (4 scenarios)
- ✅ #114: Better error messages (KeyError → descriptive exceptions)

**Deliverables**:
- ✅ Hexagonal architecture API (`@adapter`, `@service`, `Profile`)
- ✅ Complete migration guide (MIGRATION.md)
- ✅ Updated documentation (README, CLAUDE.md, MLP_VISION.md)
- ✅ 100% test coverage maintained
- ✅ Integration tests demonstrating full patterns
- ✅ Deprecation path for old API

---

## Current Sprint (0.1.0-beta) - MLP Complete

### 🎯 Sprint Goal
**"MLP Complete - Production Ready"** - API freeze, performance validation, production pilot readiness

**Timeline**: 3 weeks (Nov 25 - Dec 15, 2025)

### 📋 Work Status
**Milestone: 0.1.0-beta** (3 of 5 issues complete - 60%)

**Completed**:
1. ✅ Performance benchmarking (#18) - PR #133 merged
2. ✅ FastAPI integration example (#127) - PR #132 merged
3. ✅ Testing guide: "fakes > mocks" philosophy (#128) - PR #131 merged

**In Progress**:
- None currently

**Remaining**:
4. ⏳ MLP validation audit (#129)
5. ⏳ Release preparation (#130)

### ✅ Completed This Week (Nov 23, 2025)
**3 major features delivered**:
1. ✅ [PR #131](https://github.com/mikelane/dioxide/pull/131): Testing guide: "fakes > mocks" philosophy (#128)
   - 1,775-line comprehensive guide
   - Demonstrates dioxide's testing philosophy
   - Complete examples with fakes for all port types

2. ✅ [PR #132](https://github.com/mikelane/dioxide/pull/132): FastAPI integration example (#127)
   - Production-ready reference implementation (3,478 lines)
   - Demonstrates all MLP features in real application
   - Complete test suite (12 tests in 0.11s)

3. ✅ [PR #133](https://github.com/mikelane/dioxide/pull/133): Performance benchmarking (#18)
   - 11 comprehensive benchmarks (413 lines)
   - All targets exceeded by 30-10,000x
   - Resolution: 167-300ns (target <10μs)

### 🔄 In Progress
None currently - moving to final MLP validation

### 📝 Sprint Backlog (To Be Created)
**Week 1 (Nov 25-29)**:
- Create 0.1.0-beta milestone and issues
- FastAPI integration example implementation
- Begin performance benchmarking

**Week 2 (Dec 2-6)**:
- Complete performance benchmarking
- Testing guide documentation (fakes > mocks)
- Documentation polish

**Week 3 (Dec 9-15)**:
- MLP validation audit against MLP_VISION.md
- API reference generation
- Beta release preparation
- Release v0.1.0-beta to PyPI

---

## Milestone Progress

### 0.0.1-alpha (RELEASED ✅)
**[View milestone →](https://github.com/mikelane/dioxide/milestone/4)**

**Progress**: 100% (6 of 6 issues complete)
**Released**: Nov 6, 2025

| Issue | Status | Completed |
|-------|--------|-----------|
| #19 Singleton Caching Bug | ✅ DONE | Oct 31, 2025 |
| #20 Manual Provider Registration | ✅ DONE | Oct 31, 2025 |
| #21 Type Safety Testing | ✅ DONE | Nov 6, 2025 |
| #22 GitHub Actions CI | ✅ DONE | Nov 3, 2025 |
| #23 GitHub Actions Release | ✅ DONE | Nov 4, 2025 |
| #24 API Documentation | ✅ DONE | Nov 6, 2025 |

### 0.0.2-alpha (COMPLETE ✅)
**[View milestone →](https://github.com/mikelane/dioxide/milestone/5)**

**Progress**: 100% (11 of 11 issues complete)
**Completed**: Nov 16, 2025

| Issue | Status | Completed |
|-------|--------|-----------|
| #96 Hexagonal Architecture Epic | ✅ DONE | Nov 16, 2025 |
| #97 Container profile support | ✅ DONE | Nov 14, 2025 |
| #98 Port-based resolution | ✅ DONE | Nov 15, 2025 |
| #99 Integration tests | ✅ DONE | Nov 15, 2025 |
| #100 Documentation updates | ✅ DONE | Nov 16, 2025 |
| #101 Migration guide | ✅ DONE | Nov 16, 2025 |
| #102 Deprecation warnings | ✅ DONE | Nov 16, 2025 |
| #109 Integration test scenarios | ✅ DONE | Nov 15, 2025 |
| #114 Better error messages | ✅ DONE | Nov 16, 2025 |
| #116 Test refactoring | ✅ DONE | Nov 16, 2025 |
| #118 README migration link | ✅ DONE | Nov 16, 2025 |

**Key Deliverables**:
- ✅ Hexagonal architecture API (`@adapter.for_()`, `@service`, `Profile`)
- ✅ Complete migration guide with before/after examples
- ✅ Updated all documentation
- ✅ Maintained 100% test coverage
- ✅ Deprecation path for old `@component` API

### 0.0.3-alpha (COMPLETE ✅)
**[View milestone →](https://github.com/mikelane/dioxide/milestone/6)**

**Progress**: 100% (1 of 1 issue complete)
**Completed**: Nov 2025

| Issue | Status | Completed |
|-------|--------|-----------|
| #6 Named tokens for disambiguation | ✅ DONE | Nov 2025 |

**Note**: This milestone was for named token support, completed earlier.

### 0.0.4-alpha (COMPLETE ✅)
**[View milestone →](https://github.com/mikelane/dioxide/milestone/8)**

**Progress**: 100% (3 of 3 issues complete)
**Completed**: Nov 23, 2025
**Released**: v0.0.4-alpha.1

| Issue | Status | Completed |
|-------|--------|-----------|
| #67 @lifecycle decorator | ✅ DONE | Nov 22, 2025 |
| #5 Circular dependency detection | ✅ DONE | Nov 22, 2025 |
| #95 Lifecycle runtime support | ✅ DONE | Nov 22, 2025 |

**Key Deliverables**:
- ✅ `@lifecycle` decorator for opt-in lifecycle management
- ✅ Container lifecycle runtime (`async with container`, `start()`, `stop()`)
- ✅ Dependency-ordered initialization (Kahn's algorithm)
- ✅ Circular dependency detection at scan time
- ✅ Package scanning implementation
- ✅ Maintained 100% test coverage (92 tests passing)

### 0.1.0-beta (IN PROGRESS - MLP Complete)
**[View milestone →](https://github.com/mikelane/dioxide/milestone/9)**

**Progress**: 60% (3 of 5 issues complete)
**Target**: Dec 15, 2025

**Completed**:
1. ✅ Performance benchmarking (#18) - PR #133
2. ✅ FastAPI integration example (#127) - PR #132
3. ✅ Testing guide: "fakes > mocks" (#128) - PR #131

**Remaining**:
4. ⏳ MLP validation audit (#129)
5. ⏳ Release preparation (#130)

**Goal**: MLP feature-complete, API frozen, production-ready

---

## Remaining Work to 0.1.0-beta (MLP Complete)

### ✅ 0.0.4-alpha (COMPLETE - Nov 23, 2025)
1. ✅ @lifecycle decorator (COMPLETE)
2. ✅ Container lifecycle runtime (COMPLETE)
3. ✅ Circular dependency detection (COMPLETE)
4. ✅ Package scanning (COMPLETE)

### 0.1.0-beta (MLP Complete - Dec 15, 2025)
**Remaining work to reach MLP feature-complete**:

1. **Performance Benchmarking** (#18)
   - Measure container resolution overhead
   - Compare with other DI frameworks
   - Document performance characteristics

2. **FastAPI Integration Example**
   - Complete example application showing FastAPI + Dioxide
   - Demonstrate profile switching (production vs test)
   - Show testing with fakes pattern

3. **Testing Guide Documentation**
   - Document "fakes > mocks" philosophy
   - Provide examples of fake implementations
   - Explain when to use lifecycle vs simple fakes

4. **Documentation Polish**
   - API reference generation
   - Complete tutorial walkthrough
   - Migration guide from other frameworks

5. **MLP Validation Audit**
   - Verify all MLP_VISION.md features implemented
   - Validate against 7 guiding principles
   - Confirm API freeze readiness

**Timeline**: 3 weeks to 0.1.0-beta (Nov 25 - Dec 15, 2025)

---

## Quality Metrics

### Test Suite
- **Tests**: 92 passing ✅ (up from 29 in v0.0.1-alpha)
- **Coverage**: 100% line coverage, 100% branch coverage ✅
- **Type Safety**: mypy strict mode passing ✅

### Code Quality
- Ruff formatting: ✅ Passing
- Ruff linting: ✅ Passing
- isort: ✅ Passing
- mypy: ✅ Passing
- Cargo fmt: ✅ Passing
- Cargo clippy: ✅ Passing

### CI/CD
- **Build**: ✅ Passing on all platforms (Linux, macOS, Windows)
- **Python Versions**: ✅ 3.11, 3.13, 3.14
- **Release Automation**: ✅ Automated semantic versioning and PyPI publishing

---

## Known Issues

### Blocking 0.1.0-beta Release
- None currently - all 0.0.4-alpha features complete ✅

### 0.1.0-beta Sprint Backlog
**Must complete for MLP**:
- #18: Performance benchmarking (existing issue)
- (New): FastAPI integration example
- (New): Testing guide documentation
- (New): Documentation polish and API reference
- (New): MLP validation audit

### Post-MLP Enhancements (0.2.0+)
**Deferred to post-MLP**:
- #84: Better error messages for protocol resolution failures
- #87: Warning for empty profile matches in container.scan()
- #54: GitHub Actions audit and update
- #82: Container reset mechanism for testing isolation
- #81: Thread safety documentation
- #33: container[Type] bracket syntax (already implemented, needs docs)
- #83: Validation for @component.factory misuse

**Recently Completed**:
- ✅ #86: Package scanning (completed in v0.0.4-alpha.1)
- ✅ #64: Function injection examples (completed in v0.0.4-alpha.1)
- ✅ #67: @lifecycle decorator (completed in v0.0.4-alpha.1)
- ✅ #95: Container lifecycle runtime (completed in v0.0.4-alpha.1)
- ✅ #5: Circular dependency detection (completed in v0.0.4-alpha.1)

---

## Recent Commits

```
1c1c7bd feat: add performance benchmarking infrastructure (#18) (#133)
2dfaead docs: add comprehensive testing guide with fakes philosophy (#128) (#131)
af06d9d feat: add FastAPI integration example (#127) (#132)
882f3a2 chore(release): bump to 0.0.4-alpha.1 for PyPI filename conflict
ad4cd02 fix: correct version format to 0.0.4-alpha for Cargo semver compatibility
6a2d11c chore(release): bump version to 0.0.4-alpha
6334c71 feat: implement package scanning for container.scan() (#86) (#126)
2daa796 feat: implement container lifecycle runtime support (#95) (#125)
41ce9be docs: add comprehensive function injection examples to README (#64) (#124)
e1eddd5 chore: add Python 3.14 to package classifiers and CI matrix
```

---

## Next Actions

**This Week** (by Nov 29):
1. ✅ Complete 0.0.4-alpha milestone - DONE
2. ✅ Release v0.0.4-alpha.1 to PyPI - DONE
3. ✅ Update STATUS.md with completed sprint - DONE
4. ✅ Create 0.1.0-beta milestone on GitHub - DONE
5. ✅ Create issues for 0.1.0-beta sprint (5 issues) - DONE
6. ✅ Complete FastAPI integration example (#127) - DONE
7. ✅ Complete testing guide (#128) - DONE
8. ✅ Complete performance benchmarking (#18) - DONE

**This Weekend** (Nov 23-24):
1. ⏳ MLP validation audit (#129) - Verify all features against MLP_VISION.md
2. ⏳ Begin release preparation (#130)

**Week of Nov 25-29 (0.1.0-beta Sprint - Final Week)**:
1. Complete MLP validation audit (#129)
2. Final documentation polish (#130)
3. Prepare release notes and CHANGELOG
4. Release v0.1.0-beta to PyPI
5. API freeze announcement

**Future Milestones**:
- 0.1.0-beta: MLP complete, API freeze (Dec 15, 2025) ← **CURRENT TARGET**
- 0.2.0: Post-MLP enhancements (Q1 2026)
- 1.0.0: Stable release (Q1 2026)

---

## Documentation Status

| Document | Status | Last Updated |
|----------|--------|--------------|
| STATUS.md | ✅ Current | 2025-11-23 |
| MLP_VISION.md | ✅ Canonical | 2025-11-07 |
| ROADMAP.md | ⚠️ Needs update | Shows 0.0.3-alpha as in-progress |
| README.md | ✅ Current | 2025-11-22 |
| CLAUDE.md | ✅ Current | 2025-11-22 |
| CHANGELOG.md | ⚠️ Needs update | Missing v0.0.4-alpha.1 entry |
| DX_EVALUATION.md | ⚠️ Outdated | Still shows 70% progress |
| DOCUMENT_AUDIT.md | ⚠️ Outdated | Pre-0.0.4-alpha |
| DX_VISION.md | ✅ Aligned with MLP | 2025-11-07 |

---

## How to Use This Document

- **Updated**: Weekly on Fridays (or after major milestones)
- **Purpose**: Single source of truth for current project status
- **Audience**: Contributors, maintainers, users
- **Format**: Markdown for GitHub display

**Note**: For design specification, see [MLP_VISION.md](docs/MLP_VISION.md) (canonical). For PM assessment, see [DX_EVALUATION.md](DX_EVALUATION.md).

---

**Next Status Update**: Friday, Nov 29, 2025 (0.1.0-beta release and API freeze)

---

## MLP Progress Summary

### ✅ Completed (11 of 14 MLP Features - 79%)

**v0.0.2-alpha (Hexagonal Architecture)**:
- ✅ Hexagonal architecture API (`@adapter.for_()`, `@service`, `Profile`)
- ✅ Port-based dependency resolution
- ✅ Profile system (PRODUCTION, TEST, DEVELOPMENT, ALL)
- ✅ Complete migration guide
- ✅ Integration tests
- ✅ Deprecation warnings

**v0.0.4-alpha (Lifecycle Management)**:
- ✅ Container lifecycle runtime (`async with container`, `start()`, `stop()`)
- ✅ `@lifecycle` decorator for opt-in lifecycle management
- ✅ Dependency-ordered initialization/disposal (Kahn's algorithm)
- ✅ Circular dependency detection
- ✅ Package scanning implementation

### 📋 Remaining for MLP Complete (0 of 14 Features - 0%)

**0.1.0-beta Sprint** (Final validation remaining):
1. ✅ Performance benchmarking (#18) - DONE
2. ✅ FastAPI integration example (#127) - DONE
3. ✅ Testing guide: "fakes > mocks" philosophy (#128) - DONE

**Remaining**:
- MLP validation audit (#129) - Verify all features against MLP_VISION.md
- Release preparation (#130) - CHANGELOG, documentation polish

**Current Grade**: A+ (100/100) - 100% MLP features complete! 🎉
**Previous Grades**:
- A+ (95/100) after v0.0.4-alpha.1
- A- (85/100) after v0.0.2-alpha
- B- (75/100) after v0.0.1-alpha

**Progress**: All 14 MLP features delivered!

**Timeline to Release**: 1 week (target: Nov 29, 2025)

---

## CI/CD Infrastructure (Completed Nov 4, 2025)

### GitHub Actions CI Pipeline ✅
- **Test Matrix**: 4 Python versions (3.11, 3.12, 3.13, 3.14) × 3 OS (Ubuntu, macOS, Windows)
- **Coverage**: Codecov integration with 92.5% branch coverage requirement
- **Linting**: Python (ruff, mypy, isort) + Rust (clippy, fmt)
- **Documentation**: Sphinx build validation (fails on build errors)
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
