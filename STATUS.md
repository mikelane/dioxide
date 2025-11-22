# dioxide Project Status

**Last Updated**: 2025-11-22
**Current Milestone**: 0.0.4-alpha (Lifecycle Management)
**Latest Release**: v0.0.1-alpha (Nov 6, 2025)
**Progress**: v0.0.2-alpha COMPLETE! Hexagonal architecture API fully implemented ✅

---

## Quick Summary

🎉 **v0.0.2-alpha COMPLETE** - Hexagonal architecture API fully implemented!
✅ **11 of 11 milestone issues complete** - 100% of 0.0.2-alpha scope delivered
✅ **Breaking changes implemented** - `@adapter.for_()`, `@service`, `Profile` enum
✅ **Migration guide complete** - MIGRATION.md with comprehensive examples
🎯 **CURRENT**: 0.0.4-alpha - Lifecycle Management (#95, #67 completed, runtime support pending)

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

## Recently Completed Sprint (0.0.2-alpha) ✅

### 🎯 Sprint Goal: "Hexagonal Architecture API"
**Status**: ✅ COMPLETE (100% - 11 of 11 issues closed)

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

**Additional Work**:
- ✅ #115: Migration guide linked from README
- ✅ #116: Test suite refactoring (module-level imports)
- ✅ #117: Import organization cleanup
- ✅ #119: Deprecation warnings implementation
- ✅ #120: Descriptive error messages

**Deliverables**:
- ✅ Hexagonal architecture API (`@adapter`, `@service`, `Profile`)
- ✅ Complete migration guide (MIGRATION.md)
- ✅ Updated documentation (README, CLAUDE.md, MLP_VISION.md)
- ✅ 100% test coverage maintained
- ✅ Integration tests demonstrating full patterns
- ✅ Deprecation path for old API

## Current Sprint (0.0.4-alpha) - Lifecycle Management

### 🎯 Sprint Goal
**"Production-Ready Resource Management"** - Complete lifecycle runtime support

### 📋 Work Status
**Epic #95: Lifecycle Management & Resource Cleanup** (1/3 complete)
- ✅ Issue #67: @lifecycle decorator implementation (COMPLETE)
- ✅ Issue #5: Circular dependency detection (COMPLETE)
- ⏳ Issue #95: Runtime lifecycle support (container.start/stop, async context manager)

### 🔄 In Progress
- Epic #95: Implementing container lifecycle runtime support
  - `async with container:` context manager
  - `container.start()` / `container.stop()` methods
  - Initialize components in dependency order
  - Dispose components in reverse dependency order

### ✅ Completed Last Two Weeks (Nov 11-18, 2025)
**v0.0.2-alpha Hexagonal Architecture (11 PRs merged)**:
- PR #108: Hexagonal architecture examples
- PR #110-113: Integration test suite (basic, multi-port, chains, errors)
- PR #114: Better error messages
- PR #115: Migration guide
- PR #116-117: Test refactoring
- PR #118: Migration guide link in README
- PR #119: Deprecation warnings
- PR #120: Descriptive exceptions

**Documentation**:
- MIGRATION.md created with comprehensive before/after examples
- README.md updated with hexagonal architecture Quick Start
- CLAUDE.md updated with new API patterns
- MLP_VISION.md alignment verified

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

### 0.0.4-alpha (IN PROGRESS - Lifecycle Management)
**[View milestone →](https://github.com/mikelane/dioxide/milestone/8)**

**Progress**: 67% (2 of 3 issues complete)

| Issue | Status | Priority |
|-------|--------|----------|
| #67 @lifecycle decorator | ✅ DONE | High |
| #5 Circular dependency detection | ✅ DONE | Medium |
| #95 Lifecycle runtime support | ⏳ IN PROGRESS | High |

**Target**: Week of Nov 25, 2025
**Goal**: Production-ready resource management with container lifecycle

---

## Remaining Work to 0.1.0-beta (MLP Complete)

### 0.0.4-alpha (Current - Week of Nov 25)
1. ✅ @lifecycle decorator (COMPLETE)
2. ⏳ **Container lifecycle runtime** (#95)
   - `async with container:` context manager
   - `container.start()` / `container.stop()` methods
   - Dependency-ordered initialization/disposal

### 0.0.5-alpha (Polish & Examples)
1. Package scanning implementation (#86)
2. Complete example applications
3. FastAPI integration example
4. Error message improvements (#84, #87)
5. Documentation additions (#64, #81)

### 0.1.0-beta (API Freeze - MLP Complete)
1. Performance benchmarking (#18)
2. Final API validation
3. Complete test coverage
4. Production pilot readiness

**Timeline**: 3-4 weeks to 0.1.0-beta (Dec 16-23, 2025)

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

### Backlog (Post-MLP Enhancements)
High Priority:
- #86: Package scanning for container.scan()
- #64: Function injection examples documentation

Medium Priority:
- #84: Better error messages for protocol resolution failures
- #87: Warning for empty profile matches in container.scan()
- #54: GitHub Actions audit and update
- #82: Container reset mechanism for testing isolation
- #81: Thread safety documentation

Low Priority:
- #33: container[Type] bracket syntax (optional nice-to-have)
- #83: Validation for @component.factory misuse

---

## Recent Commits

```
0d560d9 docs: add migration guide link to README (#101) (#118)
306a89c Refactor: Move local imports to module-level in test suite (#117)
5aadfad feat: replace KeyError with descriptive error messages (#114) (#120)
1f11e6b feat: add deprecation warnings to @component API (#119)
b199662 docs: add migration guide for v0.0.1-alpha to v0.0.2-alpha (#100) (#115)
```

---

## Next Actions

**This Week** (by Nov 29):
1. ✅ Close obsolete issues (#88, #89, #94, #15, #63) - DONE
2. ✅ Update STATUS.md with correct milestones - DONE
3. ⏳ Start #95: Container lifecycle runtime implementation
4. ⏳ Write failing tests for container.start() / container.stop()
5. ⏳ Implement async context manager support

**Week of Dec 2 (Complete 0.0.4-alpha)**:
1. Complete lifecycle runtime implementation (#95)
2. Add lifecycle examples to documentation
3. Maintain 100% test coverage throughout
4. Release v0.0.4-alpha

**Week of Dec 9-16 (0.0.5-alpha - Polish)**:
1. Package scanning implementation (#86)
2. Complete example application
3. FastAPI integration example
4. Error message improvements
5. Documentation polish

**Week of Dec 16-23 (0.1.0-beta - MLP Complete)**:
1. Performance benchmarking (#18)
2. Final MLP validation against MLP_VISION.md
3. API freeze
4. Beta release to Test PyPI
5. Start production pilot program

**Future Milestones**:
- 0.0.4-alpha: Lifecycle runtime (current!)
- 0.0.5-alpha: Polish & examples (week of Dec 9)
- 0.1.0-beta: MLP complete, API freeze (week of Dec 16)
- 1.0.0: Stable release (Q1 2026)

---

## Documentation Status

| Document | Status | Last Updated |
|----------|--------|--------------|
| STATUS.md | ✅ Current | 2025-11-18 |
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

**Next Status Update**: Friday, Nov 29, 2025 (Lifecycle runtime progress)

---

## MLP Progress Summary

### ✅ Completed (v0.0.2-alpha)
- Hexagonal architecture API (`@adapter.for_()`, `@service`, `Profile`)
- Port-based dependency resolution
- Profile system (PRODUCTION, TEST, DEVELOPMENT, ALL)
- Complete migration guide
- Integration tests
- Deprecation warnings

### 🔄 In Progress (v0.0.4-alpha)
- Container lifecycle runtime (#95)
  - `async with container:` context manager
  - `container.start()` / `container.stop()` methods
  - Dependency-ordered initialization/disposal

### 📋 Remaining for MLP Complete (0.1.0-beta)
- Container lifecycle runtime (#95) - current work
- Package scanning (#86)
- Complete example application
- FastAPI integration
- Performance benchmarking (#18)

**Current Grade**: A- (85/100) - 70% complete toward MLP vision
**Previous**: B- (75/100) after v0.0.1-alpha
**Progress**: +10 points in 2 weeks! 🎉

**Timeline to MLP Complete**: 3 weeks (0.0.3-alpha → 0.0.4-alpha → 0.1.0-beta)

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
