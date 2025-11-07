# dioxide Product Roadmap

**Project**: dioxide - Make Dependency Inversion Principle feel inevitable
**Version**: 2.0.0 (MLP-aligned)
**Last Updated**: 2025-11-07
**Status**: Active Development - MLP Realignment Phase
**Canonical Reference**: [MLP_VISION.md](docs/MLP_VISION.md)

---

## ⚠️ Important: MLP Realignment

**This roadmap was rewritten on 2025-11-07** to align with the canonical MLP Vision document.

**What changed:**
- Previous roadmap (v1.1) was written **before** MLP_VISION.md existed
- 0.0.2-alpha scope changed: "Circular Dependencies" → "MLP API Realignment"
- Feature priorities reordered to match MLP north star
- Post-MLP features clearly separated

**Why:** We're in alpha with zero external users on Test PyPI. This is the perfect time to realign the API with our north star vision before anyone depends on it.

---

## Vision & Mission

### The North Star

**Make the Dependency Inversion Principle feel inevitable.**

More specifically:
> **Make it trivially easy to depend on abstractions (ports) instead of implementations (adapters), so that loose coupling becomes the path of least resistance.**

### Mission

Provide a **fast, type-safe, Pythonic** dependency injection framework that makes clean architecture the easiest choice, enabling:

1. **Type-safe DI** - If mypy passes, the wiring is correct
2. **Profile-based implementations** - Swap PostgreSQL ↔ in-memory with one line
3. **Testing without mocks** - Fast fakes at the seams, not mock behavior
4. **Zero ceremony** - Just add `@component`, scan, and go

### Market Position

- **Primary differentiator**: Makes clean architecture (ports-and-adapters) feel inevitable
- **Secondary differentiator**: Rust-backed performance
- **Target users**: Teams building maintainable Python applications
- **Philosophy**: Simplicity over features - ship the MLP, prove the value, then iterate

---

## Release Strategy

### Current Status (Nov 2025)

- **v0.0.1-alpha**: ✅ RELEASED (Nov 6, 2025) to Test PyPI
- **v0.0.2-alpha**: 🔄 IN PROGRESS - MLP API Realignment
- **Target for MLP Complete (0.1.0-beta)**: Mid-December 2025 (4-6 weeks)

### Philosophy

We follow **MLP-first development**:

1. **Alpha releases (0.0.x)**: Breaking changes acceptable - building toward MLP
2. **Beta release (0.1.0)**: MLP complete, API frozen, production-ready
3. **Post-MLP (0.2.0+)**: Ecosystem growth, framework integrations, advanced features

### Quality Gates (Every Release)

- ✅ 100% test coverage (line and branch)
- ✅ Type safety validated with mypy strict mode
- ✅ All tests passing (TDD discipline)
- ✅ Full CI/CD automation
- ✅ Documentation updated

---

## Phase 1: Alpha Series (0.0.x) - Building the MLP

**Timeline**: Nov 2025 - Early Dec 2025 (4-6 weeks)
**Goal**: Build and validate MLP as defined in MLP_VISION.md
**Status**: 🟡 In Progress

---

### 0.0.1-alpha ✅ COMPLETE

**Released**: Nov 6, 2025
**Theme**: "Walking Skeleton"
**Status**: Published to Test PyPI

**What shipped**:
- ✅ `@component` decorator for auto-discovery
- ✅ `Container.scan()` for automatic registration
- ✅ Constructor dependency injection
- ✅ SINGLETON and FACTORY scopes
- ✅ Manual provider registration
- ✅ Type-safe `Container.resolve()` with mypy support
- ✅ 100% test coverage (29 tests passing)
- ✅ Full CI/CD automation

**What we learned**:
- API doesn't match MLP Vision (was implemented before MLP doc existed)
- Missing core MLP features (profile system, lifecycle protocols, `@component.factory` syntax)
- Need API realignment before adding more features

---

### 0.0.2-alpha 🔄 IN PROGRESS

**Target**: Week of Nov 18, 2025
**Theme**: "MLP API Realignment"
**Status**: Sprint planning complete, 6 issues created

**Breaking Changes** (acceptable in alpha):
- `@component(scope=Scope.FACTORY)` → `@component.factory`
- `container = Container()` → `from dioxide import container` (global singleton)
- `container.scan()` → `container.scan("app", profile="production")`
- Add `@component.implements(Protocol)` for multiple implementations

**Core Features**:
- [ ] `@component.factory` and `@component.implements()` syntax (#28)
- [ ] `@profile` decorator system (hybrid approach) (#29)
- [ ] Update `container.scan()` with package and profile parameters (#30)
- [ ] Global singleton container pattern (#31)
- [ ] Documentation realignment (#32)
- [ ] Optional: `container[Type]` syntax (#33)

**Infrastructure**:
- [ ] Update all tests to use new API
- [ ] Maintain 100% test coverage
- [ ] Update README with MLP syntax
- [ ] Create migration guide from 0.0.1 to 0.0.2

**Success Criteria**:
- API matches MLP_VISION.md specification
- All 6 milestone issues (#28-#33) complete
- 100% test coverage maintained
- Published to Test PyPI
- Breaking changes documented

**Estimated Effort**: 2-3 weeks

**Critical Path**:
1. Implement `@component.factory` syntax (#28) - 3 days
2. Implement `@profile` system (#29) - 4 days
3. Update `container.scan()` (#30) - 2 days
4. Global singleton container (#31) - 1 day
5. Documentation realignment (#32) - 2 days
6. Optional sugar syntax (#33) - 1 day

---

### 0.0.3-alpha 📋 PLANNED

**Target**: Week of Nov 25, 2025
**Theme**: "Lifecycle Management"

**Features**:
- `Initializable` protocol for async initialization
- `Disposable` protocol for cleanup
- Async context manager support (`async with container:`)
- Lifecycle hooks called in dependency order
- Graceful shutdown in reverse dependency order

**API**:
```python
from dioxide import component, Initializable, Disposable

@component
class Database(Initializable, Disposable):
    async def initialize(self) -> None:
        self.engine = create_async_engine(self.config.database_url)

    async def dispose(self) -> None:
        await self.engine.dispose()

# Usage
async with container:
    app = container[Application]
    await app.run()
# All dispose() methods called automatically
```

**Success Criteria**:
- Lifecycle protocols implemented
- Initialize/dispose called in correct order
- Async context manager works
- No resource leaks
- Documented with examples

**Estimated Effort**: 1 week

---

### 0.0.4-alpha 📋 PLANNED

**Target**: Week of Dec 2, 2025
**Theme**: "Polish & Complete Example"

**Features**:
- Excellent error messages with suggestions
- Complete example application (notification service from MLP_VISION.md)
- FastAPI integration example
- Testing guide (fakes > mocks philosophy)
- Circular dependency detection (fail fast at startup)

**Documentation**:
- Complete example with production, test, and dev profiles
- Migration guide from other frameworks
- Testing philosophy document
- API reference
- Quick start tutorial

**Success Criteria**:
- Error messages rated 8/10+ (helpful, actionable)
- Complete example works end-to-end
- FastAPI integration documented
- Testing guide demonstrates fakes pattern
- Circular dependencies detected at scan time

**Estimated Effort**: 1 week

---

## Phase 2: MLP Complete (0.1.0-beta) - Production Ready

**Timeline**: Week of Dec 9, 2025
**Goal**: MLP feature-complete, API frozen, production-ready
**Status**: 📋 Planned

---

### 0.1.0-beta - MLP Complete 🎯

**Target**: Week of Dec 9, 2025
**Theme**: "MLP Complete - API Freeze"
**Significance**: This is the MLP milestone - feature complete and production-ready

**What "MLP Complete" means**:
- ✅ All must-have features from MLP_VISION.md implemented
- ✅ API frozen (no breaking changes until 2.0)
- ✅ Comprehensive documentation
- ✅ Testing guide with fakes > mocks philosophy
- ✅ Type-checked (mypy/pyright passes)
- ✅ Rust-backed performance
- ✅ 95%+ test coverage

**MLP Checklist** (from MLP_VISION.md):
- [x] `@component` decorator (singleton + factory) - DONE 0.0.1
- [ ] `@component.implements(Protocol)` for multiple implementations - 0.0.2
- [ ] `@profile` system with common + custom profiles - 0.0.2
- [x] Constructor injection (type-hint based) - DONE 0.0.1
- [ ] Container scanning with profile selection - 0.0.2
- [ ] Lifecycle protocols (`Initializable`, `Disposable`) - 0.0.3
- [ ] Circular dependency detection at startup - 0.0.4
- [ ] Missing dependency errors at startup - 0.0.4
- [ ] FastAPI integration example - 0.0.4
- [ ] Comprehensive documentation - 0.0.4
- [ ] Testing guide with fakes > mocks philosophy - 0.0.4
- [x] Type-checked (mypy/pyright passes) - DONE 0.0.1
- [x] Rust-backed performance - DONE 0.0.1
- [x] 95%+ test coverage - DONE 0.0.1

**Performance validation**:
- Dependency resolution < 1μs
- Container initialization < 10ms for 100 components
- Zero runtime overhead vs manual DI
- Benchmark suite

**Quality validation**:
- All tests passing
- 100% test coverage
- Type safety validated
- Security audit

**Success Criteria**:
- MLP checklist 100% complete
- Performance targets met
- Documentation rated 8/10+
- At least 5 production pilot users

**Estimated Effort**: 1 week (final validation + polish)

**After 0.1.0-beta**:
- API is frozen (semantic versioning)
- Breaking changes deferred to 2.0
- Focus shifts to ecosystem and adoption

---

## Phase 3: Post-MLP (0.2.0+) - Ecosystem Growth

**Timeline**: Q1 2026 and beyond
**Goal**: Grow ecosystem while maintaining MLP core
**Status**: 🔵 Future

---

### Guiding Principle for Post-MLP

**Before adding ANY feature, ask**:
1. Does this align with the north star? (Making DIP inevitable)
2. Can users build this themselves? (Library > framework feature)
3. Is this solving a real problem? (Not hypothetical)
4. Can we defer this to 2.0? (Simplicity over completeness)

---

### 0.2.0 - Request Scoping ⚠️ POST-MLP

**Target**: TBD Q1 2026
**Theme**: "Per-Request Lifecycle"

**Features**:
- Request-scoped components (`@component.request_scoped`)
- Scoped container context (`with container.request_scope():`)
- Multi-tenant support patterns
- Request-local state management

**Why post-MLP**: Adds complexity, can be worked around with factory scope

**Estimated Effort**: 2 weeks

---

### 0.3.0 - Property Injection ⚠️ POST-MLP

**Target**: TBD Q1 2026
**Theme**: "Alternative Injection Patterns"

**Features**:
- Property injection (`field: Type = inject()`)
- Method injection (if needed)
- Setter injection (if needed)

**Why post-MLP**: Constructor injection covers 95% of use cases

**Estimated Effort**: 1 week

---

### 0.4.0 - Advanced Patterns ⚠️ POST-MLP

**Target**: TBD Q2 2026
**Theme**: "Enterprise Features"

**Features**:
- Decorator-based AOP (aspect-oriented programming)
- Interceptors for cross-cutting concerns
- Provider functions (not just factory functions)
- Configuration providers integration

**Why post-MLP**: Advanced features that add complexity

**Estimated Effort**: 3 weeks

---

### 0.5.0 - Framework Integrations ⚠️ POST-MLP

**Target**: TBD Q2 2026
**Theme**: "Seamless Framework Integration"

**Features**:
- FastAPI official integration (`dioxide.fastapi`)
- Flask integration (`dioxide.flask`)
- Django integration (`dioxide.django`)
- Pytest plugin for testing

**Why post-MLP**: Can use manual integration patterns first

**Estimated Effort**: 4 weeks

---

### 0.6.0 - Developer Tooling ⚠️ POST-MLP

**Target**: TBD Q3 2026
**Theme**: "Developer Experience"

**Features**:
- CLI tool for container inspection
- IDE plugins (VS Code, PyCharm)
- Interactive graph visualization
- Debug mode with tracing

**Why post-MLP**: Nice-to-have, not essential for core value

**Estimated Effort**: 4 weeks

---

### 1.0.0 - Stable Release 🎯

**Target**: Q4 2026 or later
**Theme**: "Production Proven"

**Criteria for 1.0**:
- MLP proven in production (50+ deployments)
- API stable for 6+ months
- Community established (contributors, stars)
- Long-term support commitment

**Commitment**:
- Semantic versioning from 1.0 onward
- 1.x series maintains API compatibility
- Long-term support (2 years minimum)
- Security patches backported

---

## What We're NOT Building

**For MLP scope**, we explicitly exclude (see MLP_VISION.md for details):

### ❌ Configuration Management
**Why**: Use Pydantic Settings or python-decouple. Not our job.

### ❌ Property Injection (MLP)
**Why**: Constructor injection covers 95% of use cases. Adds complexity.

### ❌ Method Injection
**Why**: Rare use case, adds API surface. Use constructor injection.

### ❌ Circular Dependency Resolution
**Why**: Circular dependencies are design flaws. Don't hide them.

### ❌ XML/YAML Configuration
**Why**: Python is configuration. No external config files.

### ❌ Aspect-Oriented Programming (MLP)
**Why**: Post-MLP feature if needed. Keep MLP simple.

### ❌ Request Scoping (MLP)
**Why**: Post-MLP feature. SINGLETON and FACTORY sufficient for MLP.

---

## Success Metrics

### MLP Success Criteria (0.1.0-beta)

**Must have ALL of these**:
- [ ] Developer can set up DI in < 5 minutes
- [ ] Tests don't require mocking frameworks
- [ ] Swapping implementations takes 1 line of code
- [ ] Error messages are actionable
- [ ] Codebases naturally develop clear boundaries
- [ ] Business logic separated from I/O
- [ ] Tests are fast (no I/O)

### Adoption Metrics

| Metric | 0.0.x-alpha | 0.1-beta (MLP) | 1.0 Stable |
|--------|-------------|----------------|------------|
| Test PyPI downloads/month | 10+ | 100+ | 1,000+ |
| GitHub stars | 10+ | 100+ | 1,000+ |
| Production pilot users | 5+ | 25+ | 100+ |
| Contributors | 1-2 | 3-5 | 10+ |

### Quality Metrics (ALL Releases)

- Test coverage: 100% (line and branch)
- Type coverage: 100% (mypy strict)
- CI success rate: ≥95%
- Documentation coverage: 100% public API

### Performance Targets (Post-0.1.0)

- Dependency resolution < 1μs
- Container initialization < 10ms for 100 components
- Zero runtime overhead vs manual DI
- Memory overhead < 1MB for 1000 components

---

## Technical Roadmap

### Rust Core

**Current State** (0.0.1-alpha):
- Basic provider registration and resolution
- Singleton caching
- Type-based dependency lookup

**MLP State** (0.1.0-beta):
- Profile-aware component activation
- Lifecycle management hooks
- Circular dependency detection
- Missing dependency validation

**Post-MLP**:
- Lock-free data structures
- Memory pooling
- Parallel resolution
- Performance optimization

### Python API

**Current State** (0.0.1-alpha):
- `@component` decorator
- Instance-based Container
- Basic scanning

**MLP State** (0.1.0-beta):
- `@component.factory`, `@component.implements()`
- `@profile` system (hybrid approach)
- Global singleton container
- Lifecycle protocols

**Post-MLP**:
- Framework integrations
- Advanced patterns
- Developer tooling

---

## Risk Management

### Risk 1: MLP Realignment Complexity

**Impact**: Medium - Could delay 0.0.2-alpha
**Mitigation**:
- Breaking changes acceptable in alpha
- Zero external users on Test PyPI
- Clear migration guide from 0.0.1
**Status**: Mitigated - perfect time for realignment

### Risk 2: API Churn During Alpha

**Impact**: Low - Only affects Test PyPI users
**Mitigation**:
- Freeze API at 0.1.0-beta
- Clear versioning strategy
- Breaking changes documented
**Status**: Acceptable risk in alpha

### Risk 3: Feature Creep

**Impact**: High - Could delay MLP completion
**Mitigation**:
- Strict adherence to MLP_VISION.md
- "What We're NOT Building" list
- Defer post-MLP features to 0.2.0+
**Status**: Actively managed

### Risk 4: Performance Not Meeting Targets

**Impact**: Medium - Weakens value proposition
**Mitigation**:
- Benchmark early (0.1.0-beta)
- Set realistic targets
- Accept "significantly better" vs "10x better"
**Status**: Deferred until 0.1.0-beta

---

## Decision Log

### Decision 1: MLP Realignment (Nov 7, 2025)

**Decision**: Realign API with MLP_VISION.md in 0.0.2-alpha
**Rationale**:
- Current API doesn't match MLP specification
- Zero external users on Test PyPI
- Alpha is the right time for breaking changes
- Better to fix now than later

**Trade-offs**:
- ✅ Pro: Correct API from the start
- ✅ Pro: Minimal disruption (alpha phase)
- ❌ Con: Delays other features
- ❌ Con: Rewrites existing code

**Review Date**: Post-0.0.2-alpha

---

### Decision 2: Profile System Implementation (Nov 7, 2025)

**Decision**: Use hybrid approach (common profiles + `__getattr__` for custom)
**Rationale**:
- IDE autocomplete for common profiles (production, test, development)
- Infinite flexibility via `__getattr__` for custom profiles
- Pythonic (same pattern as `pytest.mark`)
- Zero registration required

**Trade-offs**:
- ✅ Pro: Best of both worlds
- ✅ Pro: No magic registration
- ❌ Con: Slightly more complex implementation

**Review Date**: Post-0.0.2-alpha

---

### Decision 3: Focus on MLP, Defer Post-MLP Features

**Decision**: Ship MLP (0.1.0-beta) before adding advanced features
**Rationale**:
- Prove core value proposition first
- Avoid feature creep
- Get production feedback on core
- Simplicity over completeness

**Trade-offs**:
- ✅ Pro: Faster time to MLP
- ✅ Pro: Cleaner, simpler API
- ❌ Con: Missing some "nice-to-have" features
- ❌ Con: Some users may want advanced features

**Review Date**: After 6 months of 1.0 usage

---

## Timeline Summary

```
Nov 2025:  0.0.2-alpha (MLP API Realignment)      [2-3 weeks]
           0.0.3-alpha (Lifecycle Management)      [1 week]
           0.0.4-alpha (Polish + Complete Example) [1 week]

Dec 2025:  0.1.0-beta (MLP Complete, API Freeze)  [1 week]
           ✅ MLP COMPLETE - Production Ready

Q1 2026:   Post-MLP features (0.2.0, 0.3.0, 0.4.0)
Q2 2026:   Framework integrations (0.5.0)
Q3 2026:   Developer tooling (0.6.0)
Q4 2026:   Stable release (1.0.0)
```

**Key Milestone**: 0.1.0-beta (MLP Complete) by mid-December 2025

---

## How to Use This Roadmap

**For Contributors**:
- Focus on current alpha milestone (see GitHub milestones)
- Read MLP_VISION.md before implementing
- Follow TDD discipline
- All PRs require review
- Breaking changes acceptable until 0.1.0-beta

**For Users**:
- **Alpha (0.0.x)**: Expect breaking changes, perfect for feedback
- **Beta (0.1.0)**: MLP complete, API frozen, production-ready
- **Post-MLP (0.2.0+)**: Ecosystem features, advanced patterns
- **Stable (1.0.0)**: Long-term support, proven in production

**For Product Lead**:
- Review roadmap after each alpha release
- Ensure all changes align with MLP_VISION.md
- Defer post-MLP features ruthlessly
- Celebrate MLP completion milestone

---

## Commitment Statement

**We commit to**:
- Ship the MLP (0.1.0-beta) by mid-December 2025
- Maintain focus on north star (make DIP inevitable)
- Quality over speed (100% test coverage, type safety)
- Transparent communication about roadmap changes
- Ruthlessly defer post-MLP features until MLP complete

**dioxide will be MLP-complete when all must-have features from MLP_VISION.md are implemented, tested, and documented. Not before.**

---

**Roadmap Version**: 2.0.0 (MLP-aligned)
**Last Updated**: 2025-11-07
**Next Review**: After 0.0.2-alpha release
**Canonical Reference**: [MLP_VISION.md](docs/MLP_VISION.md)
**Owner**: @mikelane (Product & Technical Lead)
