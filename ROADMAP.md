# dioxide Product Roadmap

**Project**: dioxide - Fast, Rust-backed Dependency Injection for Python
**Last Updated**: 2025-11-02
**Status**: Active Development
**Product Lead**: @mikelane

---

## Vision & Mission

### Vision
**Make dependency injection in Python as fast and safe as compiled languages while maintaining Python's simplicity and expressiveness.**

dioxide aims to be the **default choice** for Python developers who need:
- Type-safe dependency injection that works seamlessly with mypy
- Performance that scales to large codebases (1000+ components)
- Clean architecture patterns without framework lock-in
- Zero-compromise developer experience

### Mission
Provide a **production-ready, performant, and developer-friendly** DI framework that combines Python's simplicity with Rust's speed, enabling teams to build maintainable, loosely-coupled systems.

### Market Position
- **Primary competitors**: dependency-injector, injector, pinject
- **Differentiation**: Rust-backed performance, strict type safety, 100% test coverage
- **Target users**: Teams building large Python applications (APIs, data pipelines, microservices)
- **Adoption strategy**: Alpha → Beta → 1.0 with community feedback at each stage

---

## Release Strategy

### Philosophy
We follow a **transparent, iterative release process** with clear quality gates:

1. **Alpha releases** (0.0.x): Core functionality, not production-ready
2. **Beta releases** (0.x.0): Feature-complete, production-tested, API may change
3. **Release Candidates** (x.y.0-rc.N): API frozen, final validation
4. **Stable releases** (x.y.z): Production-ready, semantic versioning

### Quality Gates (Every Release)
- ✅ 100% test coverage (line and branch)
- ✅ All BDD scenarios passing
- ✅ Full CI/CD automation
- ✅ Type safety validated with mypy strict mode
- ✅ Performance benchmarks passing
- ✅ Documentation complete and accurate

---

## Phase 1: Alpha Series (0.0.x) - Foundation

**Timeline**: Q1 2025 (Jan-Mar)
**Goal**: Prove core concept with working implementation
**Status**: 🟡 In Progress

### 0.0.1-alpha (Current Sprint) - Walking Skeleton
**Target**: Week of Feb 3, 2025
**Theme**: "Make it work"

**Core Features**:
- ✅ @component decorator for auto-discovery
- ✅ Container.scan() for automatic registration
- ✅ Constructor dependency injection
- ✅ SINGLETON and FACTORY scopes (caching fixed in #19)
- ✅ Manual provider registration (register_singleton, register_factory)
- ✅ Type safety with mypy (comprehensive testing in #21)

**Infrastructure**:
- ⚠️ GitHub Actions CI/CD pipeline (in progress, see #22)
- ❌ PyPI release automation (see #23)
- ✅ 100% test coverage (verified, 29 tests passing)
- ✅ Pre-commit hooks

**Critical Path**:
1. ✅ **Issue #19: Fix Singleton Caching Bug** - COMPLETE
2. ✅ Issue #20: Manual Provider Registration - COMPLETE
3. ✅ Issue #21: Type Safety Testing - COMPLETE
4. ⚠️ Issue #22: GitHub Actions CI Workflow - IN PROGRESS
5. Issue #23: GitHub Actions Release Workflow (Est: 1 day)
6. Issue #24: API Documentation (Est: 0.5 days)

**Success Criteria**:
- Package installable via Test PyPI
- All 23 tests passing
- Works for simple DI use cases (3-5 components)
- Developer can go from install to working code in <15 minutes

**Known Limitations**:
- No circular dependency detection
- No named tokens
- No property injection
- No performance optimization

---

### 0.0.2-alpha - Circular Dependencies & Error Handling
**Target**: Week of Feb 17, 2025
**Theme**: "Make it safe"

**Features**:
- Circular dependency detection with clear error messages
- Better error messages for missing dependencies
- Validation at registration time (fail fast)
- Debug mode with verbose logging
- Optional visualization of dependency graph

**Infrastructure**:
- Mutation testing with mutmut (target: 90% mutation score)
- Performance benchmarks baseline
- Documentation site setup (MkDocs or similar)

**Success Criteria**:
- Detects circular dependencies before runtime
- Error messages guide developers to fix issues
- Mutation score ≥90%
- Performance baseline established

**Estimated Effort**: 1 week

---

### 0.0.3-alpha - Named Tokens & Disambiguation
**Target**: Week of Mar 3, 2025
**Theme**: "Make it flexible"

**Features**:
- Named tokens for disambiguation (`@component(name="primary_db")`)
- Multiple implementations of same interface
- Conditional registration based on environment
- Profile support (dev, test, prod)

**API Changes**:
```python
@component(name="primary_db")
class PostgresDB:
    pass

@component(name="cache_db")
class RedisDB:
    pass

# Resolve by name
db = container.resolve(Database, name="primary_db")
```

**Success Criteria**:
- Multiple implementations coexist
- Easy to swap implementations by environment
- No confusion when multiple providers exist

**Estimated Effort**: 1 week

---

### 0.0.4-alpha - Provider Functions & Advanced Features
**Target**: Week of Mar 17, 2025
**Theme**: "Make it powerful"

**Features**:
- Provider functions (not just factory functions)
- Property injection (not just constructor)
- Lazy initialization (defer creation until first use)
- Optional dependencies with defaults

**API Changes**:
```python
# Provider functions
@provider(scope=Scope.SINGLETON)
def database_provider(config: Config) -> Database:
    return PostgresDatabase(config.db_url)

# Property injection
@component
class UserService:
    db: Database = inject()  # Property injection
```

**Success Criteria**:
- Provider functions work alongside factory functions
- Property injection tested and documented
- Lazy initialization reduces startup time

**Estimated Effort**: 1.5 weeks

---

## Phase 2: Beta Series (0.x.0) - Production Readiness

**Timeline**: Q2 2025 (Apr-Jun)
**Goal**: Production-ready framework with proven performance
**Status**: 🔵 Planned

### 0.1.0-beta - Performance & Scale
**Target**: Week of Apr 7, 2025
**Theme**: "Make it fast"

**Performance Targets**:
- Singleton resolution: <10μs (90th percentile)
- Transient resolution: <100μs (90th percentile)
- Container.scan() for 100 components: <10ms
- Container.scan() for 1000 components: <100ms

**Optimizations**:
- Optimize Rust container for large graphs
- Cache type hint inspection results
- Parallel dependency resolution where possible
- Memory pooling for transient instances

**Benchmarks**:
- Head-to-head vs. dependency-injector
- Head-to-head vs. injector
- Scaling tests (10, 100, 1000, 10000 components)
- Memory usage profiling

**Documentation**:
- Performance tuning guide
- Benchmark results published
- Optimization best practices

**Success Criteria**:
- 10x faster than dependency-injector for large graphs
- Passes all performance targets
- Memory usage scales linearly
- Comprehensive benchmark suite

**Estimated Effort**: 2 weeks

---

### 0.2.0-beta - Lifecycle & Resource Management
**Target**: Week of Apr 28, 2025
**Theme**: "Make it robust"

**Features**:
- Graceful shutdown with reverse dependency ordering
- Async initialization support
- Context managers for resource lifecycle
- Health checks for singletons
- Auto-cleanup on container disposal

**API Changes**:
```python
@component
class Database:
    async def __ainit__(self):
        await self.connect()

    async def __aclose__(self):
        await self.disconnect()

# Async context manager
async with Container() as container:
    container.scan()
    await container.initialize()  # Calls __ainit__
    service = container.resolve(UserService)
    # ... use service
# Automatic cleanup via __aclose__
```

**Success Criteria**:
- Resources cleaned up in correct order
- No resource leaks
- Async initialization works with asyncio
- Context manager pattern tested

**Estimated Effort**: 2 weeks

---

### 0.3.0-beta - Developer Experience & Tooling
**Target**: Week of May 19, 2025
**Theme**: "Make it delightful"

**Features**:
- IDE plugins (PyCharm, VS Code)
- Interactive container inspector (`container.inspect()`)
- Graph visualization in browser
- Debug mode with tracing
- Helpful error messages with suggestions

**Tooling**:
- CLI tool for container analysis
- pytest plugin for testing with DI
- Type stub generation for better autocomplete

**Documentation**:
- Interactive tutorials
- Video walkthroughs
- Migration guides from other frameworks
- Best practices guide

**Success Criteria**:
- IDE autocomplete shows available components
- Error messages include "Did you forget to register X?"
- Graph visualization helps debug complex setups
- Documentation rated 8/10 or higher by users

**Estimated Effort**: 2 weeks

---

## Phase 3: Release Candidates (0.x.0-rc.N) - Stabilization

**Timeline**: Q3 2025 (Jul-Sep)
**Goal**: API frozen, battle-tested in production
**Status**: 🔵 Planned

### 0.4.0-rc.1 - API Freeze
**Target**: Week of Jun 9, 2025

- API frozen (no breaking changes until 2.0)
- Documentation complete
- Migration guide from 0.3 to 0.4
- Deprecation warnings for old APIs

**Estimated Effort**: 1 week

---

### 0.4.0-rc.2 through 0.4.0-rc.N - Bug Fixes Only
**Target**: Jul-Aug 2025

- Community testing period
- Bug fixes only
- Performance regression testing
- Security audit
- Production deployments tracked

**Success Criteria**:
- No critical bugs for 2 weeks
- 10+ production deployments
- No regression in benchmarks
- Security audit passed

**Estimated Effort**: 6-8 weeks

---

## Phase 4: Stable Release (1.0.0) - Production Ready

**Timeline**: Q3 2025 (Sep)
**Goal**: Stable, production-ready release
**Status**: 🔵 Planned

### 1.0.0 - Stable Release
**Target**: Week of Sep 1, 2025

**Commitment**:
- Semantic versioning from 1.0 onward
- 1.x series maintains API compatibility
- Long-term support (2 years minimum)
- Security patches backported

**Release Criteria**:
- All beta features stable
- Documentation complete
- 50+ production deployments
- <5 open critical bugs
- Community guidelines established

**Marketing**:
- Blog post announcing 1.0
- Conference talks (PyCon, PyData)
- Case studies from production users
- Comparison benchmarks published

**Success Criteria**:
- 1000+ downloads in first month
- 10+ GitHub stars per day
- Featured in Awesome Python lists
- Positive reception from community

---

## Phase 5: Post-1.0 (1.x.x Series) - Ecosystem Growth

**Timeline**: Q4 2025 and beyond
**Goal**: Build ecosystem and community
**Status**: 🔵 Future

### 1.1.0 - Framework Integrations
**Features**:
- FastAPI integration (dependency injection in routes)
- Django integration (replace Django's DI)
- Flask integration (blueprints and extensions)
- Async frameworks (Starlette, Quart)

### 1.2.0 - Advanced Patterns
**Features**:
- Decorator-based AOP (aspect-oriented programming)
- Interceptors for cross-cutting concerns
- Middleware pipeline support
- Event-driven DI with observers

### 1.3.0 - Enterprise Features
**Features**:
- Multi-tenancy support
- Configuration providers (env, YAML, JSON)
- Distributed tracing integration
- Metrics and monitoring hooks

### 2.0.0 - Breaking Changes (If Needed)
**Timeline**: 2026 or later
**Scope**: API improvements based on 1.x learnings

---

## Technical Roadmap

### Rust Core Evolution

**Current State**: Basic provider registration and resolution
**Future State**: High-performance graph algorithms

**Milestones**:
1. **petgraph Integration** (0.0.2-alpha)
   - Use petgraph for dependency graph
   - Cycle detection algorithm
   - Topological sort for initialization order

2. **Performance Optimization** (0.1.0-beta)
   - Lock-free data structures
   - Memory pooling
   - Parallel resolution

3. **Advanced Algorithms** (1.1.0+)
   - Incremental graph updates
   - Graph diffing for hot reload
   - Predictive caching

### Python API Evolution

**Current State**: Basic decorator and container
**Future State**: Rich, ergonomic API

**Milestones**:
1. **Core API Stability** (0.0.1 - 0.4.0)
   - @component decorator finalized
   - Container API complete
   - Type hints perfected

2. **Advanced APIs** (1.0.0+)
   - Plugin system
   - Custom scopes
   - Interceptors

3. **Framework Integrations** (1.1.0+)
   - Web framework adapters
   - Testing utilities
   - CLI tools

---

## Success Metrics

### Adoption Metrics
| Metric | 0.0.x-alpha | 0.x-beta | 1.0 Stable | 1.x Series |
|--------|-------------|----------|------------|------------|
| PyPI downloads/month | 100+ | 1,000+ | 10,000+ | 50,000+ |
| GitHub stars | 50+ | 200+ | 1,000+ | 5,000+ |
| Production users | 5+ | 25+ | 100+ | 500+ |
| Contributors | 2 | 5+ | 10+ | 20+ |

### Quality Metrics (All Releases)
- Test coverage: 100% (line and branch)
- Mutation score: ≥90%
- Type coverage: 100% (mypy strict)
- CI success rate: ≥95%
- Documentation coverage: 100% public API

### Performance Metrics (Post-0.1.0)
- Singleton resolution: <10μs (p90)
- Transient resolution: <100μs (p90)
- Container.scan(100): <10ms
- Container.scan(1000): <100ms
- Memory overhead: <1MB for 1000 components

### Developer Experience Metrics
- Time to first working code: <15 minutes
- Documentation satisfaction: ≥8/10
- Error message clarity: ≥8/10
- GitHub issue response time: <48 hours

---

## Risk Management

### High Risks

**Risk 1: Rust/PyO3 Complexity**
- **Impact**: Development velocity, maintainability
- **Mitigation**:
  - Keep Rust code simple and well-documented
  - Comprehensive Python test coverage
  - Rust changes require design review
- **Owner**: Technical Lead

**Risk 2: API Breaking Changes**
- **Impact**: User trust, adoption
- **Mitigation**:
  - Freeze API before 1.0
  - Deprecation policy with warnings
  - Long beta period for feedback
- **Owner**: Product Lead

**Risk 3: Performance Not Meeting Targets**
- **Impact**: Value proposition weakened
- **Mitigation**:
  - Benchmark early and often
  - Set realistic targets
  - Accept "good enough" if significantly better than alternatives
- **Owner**: Senior Developer

### Medium Risks

**Risk 4: Competition from Established Frameworks**
- **Impact**: Adoption challenges
- **Mitigation**:
  - Clear differentiation (performance + type safety)
  - Migration guides from competitors
  - Head-to-head benchmarks
- **Owner**: Product Lead

**Risk 5: Community Engagement**
- **Impact**: Slow growth, limited feedback
- **Mitigation**:
  - Active presence on Python forums
  - Conference talks and blog posts
  - Responsive to issues and PRs
- **Owner**: All team

---

## Decision Log

### Why Rust Instead of Pure Python?
**Decision**: Use Rust for performance-critical graph operations
**Rationale**:
- Dependency graphs are complex (1000+ nodes in large apps)
- Python's GIL limits concurrent resolution
- Rust provides 10-100x speedup for graph algorithms
- PyO3 provides safe, ergonomic FFI

**Trade-offs**:
- ✅ Pro: Significant performance gains
- ✅ Pro: Memory safety guarantees
- ❌ Con: Higher complexity
- ❌ Con: Slower compilation

**Review Date**: Post-1.0 (evaluate pure Python for 2.0)

---

### Why 100% Test Coverage?
**Decision**: Maintain 100% line and branch coverage
**Rationale**:
- DI frameworks are foundational (bugs cascade)
- High-stakes code needs high confidence
- Public API is small enough to cover completely

**Trade-offs**:
- ✅ Pro: High confidence in releases
- ✅ Pro: Safe refactoring
- ❌ Con: Slower feature development
- ❌ Con: Test maintenance burden

**Review Date**: Ongoing (remains policy)

---

### Why Alpha → Beta → RC → Stable?
**Decision**: Follow traditional release cadence
**Rationale**:
- Sets clear expectations (alpha = unstable)
- Allows API iteration without breaking trust
- Beta period gathers production feedback

**Trade-offs**:
- ✅ Pro: Users know what to expect
- ✅ Pro: Safe to break API in alpha/beta
- ❌ Con: Slower to reach "stable" label
- ❌ Con: Some users won't adopt until 1.0

**Review Date**: After 0.4.0-rc.1 (evaluate pace)

---

## Open Questions

### For Alpha Phase
1. Should we support Python 3.10? (Currently 3.11+)
2. Should we publish to PyPI or only Test PyPI during alpha?
3. Should circular dependency detection be in 0.0.1 or 0.0.2?

### For Beta Phase
1. What's the right balance between features and stability?
2. Should we prioritize performance or ergonomics first?
3. How many production deployments before 1.0?

### For 1.0+
1. Should we target corporate sponsors for sustainability?
2. Should we create a Discord/Slack community?
3. Should we pursue Python Software Foundation affiliation?

---

## How to Use This Roadmap

**For Contributors**:
- Pick issues from current sprint milestone
- Read design docs before implementing
- Follow BDD/TDD discipline
- All PRs require review

**For Users**:
- Alpha releases: Try it, break it, give feedback
- Beta releases: Test in staging environments
- RC releases: Deploy to production with caution
- Stable releases: Safe for production

**For Product Lead**:
- Review roadmap quarterly
- Adjust based on feedback
- Communicate changes transparently
- Celebrate milestones with team

---

## Commitment Statement

**I commit to**:
- Transparent roadmap updates
- Listening to community feedback
- Quality over speed
- Clear, actionable milestones
- Celebrating team wins

**dioxide will be production-ready when it's ready, not before.**

---

**Next Review Date**: End of 0.0.1-alpha sprint (Week of Feb 3, 2025)

**Roadmap Version**: 1.1
**Last Updated**: 2025-11-02
**Owner**: @mikelane (Product & Technical Lead)
