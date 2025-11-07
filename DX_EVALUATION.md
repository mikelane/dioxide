# Dioxide: PM Assessment Against MLP Vision

**Assessment Date**: 2025-11-07
**Assessor**: Product-Technical Lead
**Current Release**: v0.0.1-alpha (Released Nov 6, 2025)
**Assessment Type**: Strategic alignment check against MLP_VISION.md

---

## Executive Summary

### 🎯 Strategic Alignment: **PARTIALLY ALIGNED**

**Overall Grade: B- (75/100)**

dioxide has made excellent progress on **implementation fundamentals** (DI mechanics, quality, testing) but has **significant API misalignment** with the MLP Vision document. The current implementation represents a solid "basic DI framework" but is NOT architected according to the MLP north star.

### Key Findings

**✅ What's Working Well:**
- Core DI mechanics are solid (registration, resolution, scoping)
- Quality is excellent (100% coverage, CI/CD, type safety)
- Rust integration working smoothly
- Test discipline is strong
- Project management infrastructure in place

**❌ Critical Gaps from MLP Vision:**
- API design does not match MLP specification
- Profile system completely missing (cornerstone of MLP)
- Lifecycle protocols missing
- Container pattern differs from vision (instance vs global singleton)
- Syntax for key features differs from specification

**⚠️ Risk Assessment:**
- **HIGH RISK**: Continuing on current path will create technical debt
- **HIGH RISK**: Current API will require breaking changes to align with MLP
- **MEDIUM RISK**: Roadmap is based on pre-MLP vision

### Recommendation

**PAUSE FEATURE DEVELOPMENT. REALIGN WITH MLP VISION.**

We are at v0.0.1-alpha - this is the PERFECT time to make breaking changes and realign. The longer we wait, the more expensive the realignment becomes.

---

## Detailed Gap Analysis

### 1. Core API Design

#### Current Implementation vs MLP Vision

| Feature | MLP Vision | Current Implementation | Status | Priority |
|---------|-----------|----------------------|--------|----------|
| @component decorator | `@component` (singleton default) | `@component` ✅ | ✅ ALIGNED | - |
| Factory scope syntax | `@component.factory` | `@component(scope=Scope.FACTORY)` | ❌ MISALIGNED | **P0** |
| Protocol implementation | `@component.implements(EmailProvider)` | Not implemented | ❌ MISSING | **P0** |
| Container as global singleton | `from dioxide import container` | `container = Container()` | ❌ MISALIGNED | **P0** |
| Container scan with profile | `container.scan("app", profile="production")` | `container.scan()` | ❌ MISALIGNED | **P0** |
| Resolution syntax | `container[UserService]` | `container.resolve(UserService)` | ❌ MISALIGNED | P1 |

**Assessment**: 🔴 **CRITICAL MISALIGNMENT** - Core API differs significantly from MLP specification

#### Example: Current vs MLP

**Current Implementation:**
```python
from dioxide import Container, component, Scope

@component(scope=Scope.FACTORY)  # ❌ Wrong syntax per MLP
class RequestHandler:
    def __init__(self, service: UserService):
        self.service = service

container = Container()  # ❌ Shouldn't instantiate per MLP
container.scan()  # ❌ Missing profile parameter per MLP
handler = container.resolve(RequestHandler)  # ❌ Wrong syntax per MLP
```

**MLP Vision:**
```python
from dioxide import container, component

@component.factory  # ✅ MLP syntax
class RequestHandler:
    def __init__(self, service: UserService):
        self.service = service

container.scan("app", profile="production")  # ✅ MLP syntax
handler = container[RequestHandler]  # ✅ MLP syntax
```

**Impact**: Breaking API changes required to align with MLP

---

### 2. Profile System (MISSING)

#### MLP Vision: Core Feature

The profile system is a **cornerstone feature** of the MLP vision, enabling:
- Environment-specific implementations (production, test, development)
- Fakes at the seams testing philosophy
- Zero-ceremony environment switching

#### Current Status: **COMPLETELY MISSING**

**Impact Rating**: 🔴 **CRITICAL**

The profile system is mentioned throughout MLP_VISION.md:
- Section 4: "Profile System" (entire section)
- Section 5: "Testing Philosophy" (depends on profiles)
- Section 6: "Framework Integration" (uses profiles)
- Section 8: "Complete Example" (profiles everywhere)
- Section 9: "Success Metrics" - MLP checklist includes "✅ @profile system"

**Current Roadmap**: Profile system appears in ROADMAP.md as "0.0.3-alpha - Named Tokens & Disambiguation" but:
1. It's positioned as "profiles" not "@profile decorator"
2. It's scheduled THIRD, but MLP says it's core
3. The design doesn't match MLP specification

**Recommendation**:
- Implement `@profile` decorator system IMMEDIATELY after API realignment
- Follow MLP hybrid approach (common profiles + `__getattr__` for custom)
- Target for 0.0.2-alpha, NOT 0.0.3

---

### 3. Lifecycle Protocols (MISSING)

#### MLP Vision: Section 3 - "Lifecycle: Protocols Over Decorators"

```python
from dioxide import component, Initializable, Disposable

@component
class Database(Initializable, Disposable):
    async def initialize(self) -> None:
        """Called by container.start() or async with container"""
        self.engine = create_async_engine(...)

    async def dispose(self) -> None:
        """Called by container.stop() or async with exit"""
        await self.engine.dispose()
```

#### Current Status: **COMPLETELY MISSING**

**Impact Rating**: 🔴 **CRITICAL**

Lifecycle management is essential for:
- Database connections
- File handles
- Background tasks
- Resource cleanup

**MLP Requirements**:
- `Initializable` protocol with `async def initialize()`
- `Disposable` protocol with `async def dispose()`
- `async with container:` context manager support
- Automatic lifecycle orchestration

**Current State**: None of this exists

**Recommendation**: Implement in 0.0.3-alpha (after profiles)

---

### 4. Container Pattern Mismatch

#### MLP Vision: Global Singleton

```python
from dioxide import container  # ✅ Global singleton, never instantiate

container.scan("app", profile="production")
service = container[UserService]
```

**Rationale from MLP**: "No passing container around"

#### Current Implementation: Instance-based

```python
from dioxide import Container  # ❌ Class you instantiate

container = Container()  # ❌ Must instantiate
container.scan()
service = container.resolve(UserService)
```

**Impact Rating**: 🟡 **MEDIUM** (works, but not aligned with philosophy)

**Pros of current approach**:
- Easier to test (multiple containers)
- More explicit
- No global state

**Cons of current approach**:
- Violates MLP principle #2: "Explicit Over Clever"
- MLP says: "The container is a global singleton. You never instantiate it."
- More ceremony (passing container around)

**Recommendation**:
- Create global singleton `container` instance in `__init__.py`
- Keep `Container` class for advanced use cases / testing
- Update all docs to show singleton pattern
- Schedule for 0.0.2-alpha (API realignment sprint)

---

### 5. Syntax Differences

| MLP Vision | Current Implementation | Impact |
|-----------|----------------------|--------|
| `@component.factory` | `@component(scope=Scope.FACTORY)` | 🔴 Breaking change needed |
| `@component.implements(EmailProvider)` | Not supported | 🔴 Missing feature |
| `@profile.production` | Not supported | 🔴 Missing feature |
| `@profile.test` | Not supported | 🔴 Missing feature |
| `@profile("prod", "staging")` | Not supported | 🔴 Missing feature |
| `container.scan("app", profile=...)` | `container.scan()` | 🔴 Breaking change needed |
| `container[Type]` | `container.resolve(Type)` | 🟡 Nice-to-have |
| `async with container:` | Not supported | 🔴 Missing feature |

**Assessment**: Multiple breaking changes required to align with MLP

---

### 6. Testing Philosophy Alignment

#### MLP Vision: "Fakes at the Seams"

**Philosophy from MLP_VISION.md Section 5**:
- Use fast, real implementations instead of mocks
- Fakes live in PRODUCTION code, not test code
- Profile system enables swapping implementations
- In-memory implementations for testing/dev

#### Current Implementation

**Status**: ✅ **PHILOSOPHY ALIGNED** but 🔴 **INFRASTRUCTURE MISSING**

We follow the philosophy (tests use real implementations), but:
- No profile system to make this easy
- No example fakes in the codebase
- No guidance on how to structure fakes

**Recommendation**:
- Create example fakes after profile system implemented
- Add to documentation as a core pattern
- Include in complete example

---

## What We Got Right

### ✅ 1. Core DI Mechanics

**Aligned with MLP Principles**:
- Type-checker is source of truth (principle #1) ✅
- Constructor injection working ✅
- Singleton and factory scopes implemented ✅
- Type safety with mypy ✅
- Fast resolution via Rust ✅

### ✅ 2. Quality Standards

**Aligned with MLP Success Metrics**:
- 100% test coverage ✅
- BDD/TDD discipline ✅
- CI/CD automation ✅
- Pre-commit hooks ✅
- Clean codebase ✅

### ✅ 3. Rust Integration

**Aligned with MLP Principle #7** ("Performance is Not a Tradeoff"):
- PyO3 working smoothly ✅
- Singleton caching in Rust ✅
- Type-safe resolution ✅
- Build pipeline working ✅

### ✅ 4. What We're NOT Building

**Correctly excluded from MLP**:
- ✅ Configuration management (use Pydantic)
- ✅ Property injection (constructor only)
- ✅ Method injection (constructor only)
- ✅ Circular dependency resolution with Provider[T]
- ✅ XML/YAML configuration
- ✅ AOP (post-MLP)
- ✅ Request scoping (post-MLP)

Good restraint shown - not overbuilding!

---

## What Needs to Change

### 🔴 Priority 0 (Blocking MLP) - API Realignment Sprint

**Target**: 0.0.2-alpha
**Estimated Effort**: 2-3 weeks
**Breaking Changes**: YES (acceptable in alpha)

#### Changes Required:

1. **Add `@component.factory` syntax**
   ```python
   # Before (current)
   @component(scope=Scope.FACTORY)
   class Handler: pass

   # After (MLP)
   @component.factory
   class Handler: pass
   ```
   - Keep `@component(scope=...)` for backwards compat during alpha
   - Deprecate in 0.1.0-beta

2. **Add `@component.implements(Protocol)` syntax**
   ```python
   from typing import Protocol

   class EmailProvider(Protocol):
       async def send(self, to: str, subject: str, body: str) -> None: ...

   @component.implements(EmailProvider)
   @profile.production
   class SendGridEmail:
       async def send(self, to: str, subject: str, body: str) -> None:
           # Real implementation
           pass
   ```
   - Track which protocol(s) each component implements
   - Use for profile-based resolution

3. **Add profile system**
   ```python
   # dioxide/profile.py
   class ProfileMarker:
       production: 'ProfileDecorator'
       test: 'ProfileDecorator'
       development: 'ProfileDecorator'
       staging: 'ProfileDecorator'

       def __getattr__(self, name: str):
           """Catch-all for custom profiles"""
           return self._make_decorator(name)

       def __call__(self, *names: str):
           """Multiple profiles"""
           def decorator(cls):
               cls.__dioxide_profiles__ = set(names)
               return cls
           return decorator

   profile = ProfileMarker()
   ```

4. **Add package scanning to `container.scan()`**
   ```python
   # Before (current)
   container.scan()

   # After (MLP)
   container.scan("app", profile="production")
   ```
   - `package` parameter: Root package to scan for `@component` classes
   - `profile` parameter: Active profile (filters by `@profile` decorator)

5. **Add global singleton container**
   ```python
   # dioxide/__init__.py
   _global_container = Container()

   # Export as singleton
   container = _global_container

   __all__ = [
       'container',  # Global singleton
       'Container',  # Class for advanced use
       # ...
   ]
   ```

6. **Optional: Add `container[Type]` syntax**
   ```python
   class Container:
       def __getitem__(self, component_type: type[T]) -> T:
           """Allow container[Type] syntax"""
           return self.resolve(component_type)
   ```

---

### 🟡 Priority 1 (Required for MLP) - Lifecycle Management

**Target**: 0.0.3-alpha
**Estimated Effort**: 1-2 weeks

#### Changes Required:

1. **Add lifecycle protocols**
   ```python
   # dioxide/lifecycle.py
   from typing import Protocol

   class Initializable(Protocol):
       async def initialize(self) -> None: ...

   class Disposable(Protocol):
       async def dispose(self) -> None: ...
   ```

2. **Add async context manager support**
   ```python
   class Container:
       async def __aenter__(self):
           await self.initialize()
           return self

       async def __aexit__(self, exc_type, exc_val, exc_tb):
           await self.dispose()

       async def initialize(self):
           """Call initialize() on all Initializable components"""
           for component in self._initialized_components:
               if isinstance(component, Initializable):
                   await component.initialize()

       async def dispose(self):
           """Call dispose() on all Disposable components (reverse order)"""
           for component in reversed(self._initialized_components):
               if isinstance(component, Disposable):
                   await component.dispose()
   ```

---

### 🟢 Priority 2 (Nice to Have for MLP) - Error Handling

**Target**: 0.0.4-alpha
**Estimated Effort**: 1 week

1. **Circular dependency detection** (already on roadmap)
   - Use petgraph for cycle detection
   - Clear error messages showing cycle path
   - Fail at scan() time, not resolve() time

2. **Better error messages**
   - "Did you forget to register X?"
   - "Did you forget to add @component decorator?"
   - "Profile 'test' is active but X is only registered for 'production'"

---

## Roadmap to MLP: Revised Plan

### Current Position
- ✅ v0.0.1-alpha released (Nov 6, 2025)
- 🔴 API misaligned with MLP vision
- 🔴 Profile system missing
- 🔴 Lifecycle management missing

### Recommended Path Forward

#### Sprint 1: API Realignment (0.0.2-alpha)
**Duration**: 2-3 weeks
**Goal**: Align API with MLP vision

**Tasks**:
1. Implement `@component.factory` syntax
2. Implement `@component.implements(Protocol)` syntax
3. Implement `@profile` decorator system (hybrid approach)
4. Update `container.scan()` to accept package and profile
5. Create global singleton container pattern
6. Optional: Add `container[Type]` syntax
7. Update all tests to use new syntax
8. Update all documentation
9. Add migration guide from 0.0.1 to 0.0.2

**Breaking Changes**: YES (acceptable in alpha)

**Success Criteria**:
- API matches MLP_VISION.md specification
- Profile system working (production, test, development, custom)
- All existing functionality preserved (just different syntax)
- 100% test coverage maintained
- Documentation updated

#### Sprint 2: Lifecycle Management (0.0.3-alpha)
**Duration**: 1-2 weeks
**Goal**: Add lifecycle protocols and async context manager

**Tasks**:
1. Implement `Initializable` protocol
2. Implement `Disposable` protocol
3. Implement async context manager support
4. Track initialization order
5. Implement reverse-order disposal
6. Add comprehensive lifecycle tests
7. Document lifecycle patterns

**Success Criteria**:
- `async with container:` pattern working
- Components initialize in dependency order
- Components dispose in reverse order
- No resource leaks
- Documented with examples

#### Sprint 3: Polish & Complete Example (0.0.4-alpha)
**Duration**: 1 week
**Goal**: Complete MLP checklist and create comprehensive example

**Tasks**:
1. Circular dependency detection (from backlog)
2. Better error messages
3. Create complete example (like in MLP_VISION.md)
4. Add example fakes (FakeEmail, FakeClock, InMemoryRepo)
5. FastAPI integration example
6. Update README with MLP philosophy
7. Final documentation pass

**Success Criteria**:
- All MLP checklist items complete ✅
- Complete example runs and demonstrates all features
- Documentation clearly explains philosophy
- Ready for beta testing

#### Sprint 4: Beta Preparation (0.1.0-beta)
**Duration**: 1 week
**Goal**: API freeze and production readiness

**Tasks**:
1. API freeze (no more breaking changes)
2. Performance benchmarking
3. Security audit
4. Community feedback collection
5. Migration guide for alpha users
6. Publish to real PyPI (not test instance)

**Success Criteria**:
- API stable
- Performance meets targets
- No critical security issues
- Positive community feedback
- Production-ready

---

## MLP Checklist: Current Status

From MLP_VISION.md Section 9 - "Must-Have Features for MLP":

| Feature | Status | Target Sprint |
|---------|--------|--------------|
| ✅ `@component` decorator (singleton + factory) | ⚠️ Partial (wrong syntax) | 0.0.2-alpha |
| ✅ `@component.implements(Protocol)` | ❌ Missing | 0.0.2-alpha |
| ✅ `@profile` system with common + custom profiles | ❌ Missing | 0.0.2-alpha |
| ✅ Constructor injection (type-hint based) | ✅ Complete | - |
| ✅ Container scanning with profile selection | ⚠️ Partial (no profile param) | 0.0.2-alpha |
| ✅ Lifecycle protocols (`Initializable`, `Disposable`) | ❌ Missing | 0.0.3-alpha |
| ✅ Circular dependency detection at startup | ❌ Missing (tests skipped) | 0.0.4-alpha |
| ✅ Missing dependency errors at startup | ✅ Complete | - |
| ✅ FastAPI integration example | ❌ Missing | 0.0.4-alpha |
| ✅ Comprehensive documentation | ⚠️ Partial (needs MLP update) | 0.0.4-alpha |
| ✅ Testing guide with fakes > mocks philosophy | ❌ Missing | 0.0.4-alpha |
| ✅ Type-checked (mypy/pyright passes) | ✅ Complete | - |
| ✅ Rust-backed performance | ✅ Complete | - |
| ✅ 95%+ test coverage | ✅ Complete (100%) | - |

**Current Score**: 5/14 complete (36%)
**Target for MLP**: 14/14 complete (100%)

**Estimated Time to MLP**: 4-5 sprints (8-12 weeks)

---

## Risk Assessment

### 🔴 HIGH RISKS

**Risk 1: Breaking Changes in Alpha**
- **Impact**: Users on 0.0.1-alpha will need to migrate
- **Likelihood**: Certain (API realignment required)
- **Mitigation**:
  - Clear communication about alpha instability
  - Comprehensive migration guide
  - Deprecation warnings in 0.0.1 → 0.0.2
  - Only 5-10 external users likely on Test PyPI
- **Accept/Mitigate**: ACCEPT (alpha is for breaking changes)

**Risk 2: Roadmap Needs Rewrite**
- **Impact**: Current ROADMAP.md is misaligned
- **Likelihood**: Certain
- **Mitigation**:
  - Rewrite ROADMAP.md to match MLP priorities
  - Communicate change transparently
  - Update all planning docs
- **Accept/Mitigate**: MITIGATE (action item)

### 🟡 MEDIUM RISKS

**Risk 3: Profile System Complexity**
- **Impact**: Profile system is complex feature
- **Likelihood**: Medium
- **Mitigation**:
  - Follow MLP design exactly (proven pattern from Spring)
  - Start simple (just production/test/dev)
  - Add `__getattr__` magic later
  - Comprehensive testing
- **Accept/Mitigate**: MITIGATE (design carefully)

**Risk 4: Timeline Pressure**
- **Impact**: 8-12 weeks to realign might feel slow
- **Likelihood**: Medium
- **Mitigation**:
  - Quality over speed (MLP must be right)
  - Alpha is time for iteration
  - Clear communication of progress
- **Accept/Mitigate**: ACCEPT (we're in alpha)

---

## Recommendations

### Immediate Actions (This Week)

1. **PAUSE new feature development**
   - Don't continue with 0.0.2-alpha circular dependency work
   - Reassess priorities based on MLP vision

2. **Create GitHub issues for MLP alignment**
   - Issue: "API Realignment: Implement @component.factory syntax"
   - Issue: "API Realignment: Implement @component.implements(Protocol)"
   - Issue: "Feature: Implement @profile decorator system"
   - Issue: "Feature: Add package scanning to container.scan()"
   - Issue: "Feature: Create global singleton container"
   - Issue: "Feature: Implement lifecycle protocols"
   - Issue: "Documentation: Rewrite ROADMAP.md for MLP alignment"

3. **Update STATUS.md**
   - Reflect decision to realign with MLP
   - Update sprint plan for 0.0.2-alpha
   - Set realistic timeline (2-3 weeks for API realignment)

4. **Communicate with stakeholders**
   - If any external users, notify about API changes
   - Update GitHub README with "API in flux during alpha"

### Strategic Decisions Needed

**Decision 1**: Accept Breaking Changes?
- **Recommendation**: YES - we're in alpha, this is the time
- **Rationale**: Cost of change increases exponentially with user base
- **Action**: Approve breaking changes for 0.0.2-alpha

**Decision 2**: Follow MLP Vision Strictly?
- **Recommendation**: YES - it's our north star
- **Rationale**: MLP document is well-thought-out and proven patterns
- **Action**: Treat MLP_VISION.md as canonical (already stated in doc)

**Decision 3**: Rewrite ROADMAP?
- **Recommendation**: YES - current roadmap is pre-MLP
- **Rationale**: Roadmap phases don't align with MLP priorities
- **Action**: Create ROADMAP_v2.md based on MLP

### Long-term Success Factors

**What We Need to Succeed**:
1. ✅ Strong commitment to quality (we have this)
2. ✅ Clear vision document (MLP_VISION.md is excellent)
3. ⚠️ Alignment between vision and implementation (fixing this)
4. ⚠️ Roadmap matching MLP priorities (fixing this)
5. ✅ Technical capability (proven with 0.0.1-alpha)
6. ⚠️ Realistic timeline (adjusting)

**Confidence Level**: 🟢 **HIGH** once realigned

The fundamentals are solid. We just need to realign the implementation with the vision. Being in alpha is the perfect time to do this.

---

## Conclusion

### Summary Assessment

dioxide v0.0.1-alpha demonstrates **strong technical execution** but **incomplete alignment** with the MLP vision. The team has built a solid foundation with excellent quality practices, but the API design and feature set don't match the canonical MLP_VISION.md specification.

### Critical Path to MLP

```
Current State (0.0.1-alpha)
    ↓
API Realignment (0.0.2-alpha) ← 2-3 weeks
    ↓
Lifecycle Management (0.0.3-alpha) ← 1-2 weeks
    ↓
Complete Example & Polish (0.0.4-alpha) ← 1 week
    ↓
MLP Complete (0.1.0-beta) ← 1 week
```

**Total Estimated Time**: 5-7 weeks

### Recommendation

**REALIGN NOW** while we're in alpha. The cost of change is low (few external users), the benefits are high (correct architecture), and the timing is perfect (alpha is for breaking changes).

### Final Grade

**Current State**: B- (75/100)
- Quality: A+ (100%)
- Technical execution: A (95%)
- API alignment: C (60%)
- Feature completeness vs MLP: D+ (36%)

**Potential State** (post-realignment): A (95/100)
- Everything solid + aligned with vision

---

## Action Items

### For Product-Technical Lead

- [ ] Review this assessment
- [ ] Make go/no-go decision on API realignment
- [ ] Approve revised roadmap
- [ ] Communicate plan to team/stakeholders
- [ ] Create GitHub issues for MLP work
- [ ] Update STATUS.md with new sprint plan
- [ ] Schedule: Aim for 0.0.2-alpha by end of November 2025

### For Development Team

- [ ] Pause work on current 0.0.2-alpha scope (circular dependencies)
- [ ] Wait for go/no-go decision
- [ ] If approved: Begin API realignment sprint
- [ ] Maintain 100% test coverage through transition
- [ ] Update documentation as API changes

### For Documentation

- [ ] Create migration guide: 0.0.1 → 0.0.2
- [ ] Rewrite ROADMAP.md to match MLP priorities
- [ ] Update README to show MLP-aligned examples
- [ ] Add "API in flux during alpha" warning

---

**Document Version**: 1.0
**Next Review**: After 0.0.2-alpha sprint planning
**Owner**: Product-Technical Lead (@mikelane)
