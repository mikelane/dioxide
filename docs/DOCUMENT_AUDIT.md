# Document Audit: MLP Vision Alignment

**Audit Date**: 2025-11-07
**Purpose**: Identify documents that conflict with MLP_VISION.md
**Action**: Update or deprecate conflicting documents

---

## Source of Truth

**MLP_VISION.md** (`docs/MLP_VISION.md`) is the canonical design document.
- Created: 2025-11-07
- Version: 1.0.0 MLP
- Status: Canonical

All other documents must align with MLP Vision or be clearly marked as outdated/deprecated.

---

## Document Status

### 🟢 ALIGNED - No Changes Needed

#### docs/MLP_VISION.md
- **Status**: ✅ Source of Truth
- **Action**: None

#### docs/design/singleton-caching-fix.md
- **Status**: ✅ Technical design doc, aligned
- **Content**: Bug fix for Rust singleton caching
- **Action**: None (implementation detail, not API)

#### docs/design/github-actions-ci.md
- **Status**: ✅ Infrastructure doc, aligned
- **Content**: CI/CD pipeline design
- **Action**: None (infrastructure, not API)

#### docs/design/github-actions-release.md
- **Status**: ✅ Infrastructure doc, aligned
- **Content**: Release pipeline design
- **Action**: None (infrastructure, not API)

#### docs/cicd-modernization-plan.md
- **Status**: ✅ Infrastructure doc, aligned
- **Content**: CI/CD modernization strategy
- **Action**: None (infrastructure, not API)

#### COVERAGE.md
- **Status**: ✅ Process doc, aligned
- **Content**: Testing and coverage strategy
- **Action**: None (process, not API)

#### CONTRIBUTING.md
- **Status**: ✅ Process doc, aligned
- **Content**: Contribution guidelines
- **Action**: None (process, not API)

#### CHANGELOG.md
- **Status**: ✅ Historical record, aligned
- **Content**: Version history
- **Action**: None (historical record)

---

### 🟡 PARTIALLY ALIGNED - Needs Update

#### README.md
- **Status**: ⚠️ Shows pre-MLP API examples
- **Conflicts**:
  - Shows instance-based Container pattern: `container = Container()`
  - Shows `container.scan()` without profile parameter
  - No mention of `@profile` system
  - No mention of lifecycle protocols
  - Quick start example doesn't match MLP syntax
- **Action**: **UPDATE** to show MLP API examples
- **Priority**: P0 (user-facing)
- **Estimated Effort**: 1 hour

**Example conflict:**
```python
# Current README (pre-MLP)
container = Container()
container.register_value('connection_string', 'postgresql://localhost/mydb')

# Should be (MLP)
from dioxide import container
container.scan("app", profile="production")
```

#### CLAUDE.md (Project Instructions)
- **Status**: ⚠️ References pre-MLP API
- **Conflicts**:
  - Example shows `container = Container()` pattern
  - No mention of profile system
  - Quick start example outdated
- **Action**: **UPDATE** project instructions to reference MLP
- **Priority**: P1 (developer-facing)
- **Estimated Effort**: 30 minutes

#### STATUS.md
- **Status**: ⚠️ Sprint planning based on pre-MLP roadmap
- **Conflicts**:
  - 0.0.2-alpha scope is "circular dependencies"
  - Should be "API realignment + profile system" per MLP
  - Milestone descriptions don't mention MLP features
- **Action**: **UPDATE** to reflect MLP-aligned sprint plan
- **Priority**: P0 (project management)
- **Estimated Effort**: 30 minutes

---

### 🔴 MISALIGNED - Needs Major Rewrite

#### ROADMAP.md
- **Status**: ✅ Rewritten and aligned (2025-11-07)
- **Action**: **COMPLETE** - Entire roadmap rewritten based on MLP priorities
- **Changes Made**:
  - Complete rewrite from scratch (v1.1 → v2.0.0)
  - 0.0.2-alpha: "Circular Dependencies" → "MLP API Realignment"
  - 0.0.3-alpha: "Named Tokens" → "Lifecycle Management"
  - 0.0.4-alpha: "Provider Functions" → "Polish + Complete Example"
  - 0.1.0-beta: "Performance" → "MLP Complete" (API freeze milestone)
  - Post-MLP features clearly separated (0.2.0+)
  - Timeline: MLP complete by mid-December 2025
  - All API examples use MLP syntax
  - References MLP_VISION.md as canonical source
- **Priority**: Completed

**Key conflicts:**
```
Current Roadmap Phase Order:
1. 0.0.2: Circular Dependencies ❌
2. 0.0.3: Named Tokens ❌ (wrong framing)
3. 0.0.4: Provider Functions ❌ (not in MLP)

MLP-Aligned Phase Order Should Be:
1. 0.0.2: API Realignment + Profile System ✅
2. 0.0.3: Lifecycle Management ✅
3. 0.0.4: Polish + Complete Example ✅
4. 0.1.0-beta: MLP Complete ✅
```

#### docs/0.0.1-ALPHA_SCOPE.md
- **Status**: ❌ Reflects pre-MLP feature set
- **Conflicts**:
  - Success criteria don't mention MLP alignment
  - Feature descriptions use pre-MLP terminology
  - No mention of profile system as critical gap
  - Issue tracking refers to pre-MLP priorities
- **Action**: **MARK AS HISTORICAL** and create new scope docs for future releases
- **Priority**: P2 (historical reference)
- **Estimated Effort**: 15 minutes to add deprecation notice

#### docs/RELEASE_CHECKLIST_0.0.1-alpha.md
- **Status**: ❌ Pre-MLP release checklist
- **Conflicts**:
  - Definition of done doesn't include MLP features
  - Success criteria pre-MLP
- **Action**: **MARK AS HISTORICAL** and create MLP-aligned checklists
- **Priority**: P2 (historical reference)
- **Estimated Effort**: 15 minutes to add deprecation notice

---

### 🔵 NEEDS REVIEW

#### docs/design/ADR-001-container-architecture.md
- **Status**: 🔵 Need to review
- **Potential Conflicts**: May specify instance-based container pattern
- **Action**: **REVIEW** and potentially update or supersede with new ADR
- **Priority**: P1

#### docs/design/ADR-002-pyo3-binding-strategy.md
- **Status**: 🔵 Need to review
- **Potential Conflicts**: May need update for profile system
- **Action**: **REVIEW** for MLP compatibility
- **Priority**: P2

#### docs/DEVELOPER_EXPERIENCE.md
- **Status**: 🔵 Need to review
- **Content**: DX principles and patterns
- **Action**: **REVIEW** to ensure DX vision aligns with MLP
- **Priority**: P1

#### docs/DX_VISION.md
- **Status**: ✅ Reviewed and aligned
- **Content**: Aspirational DX vision document
- **Action**: **ALIGNED** - Updated to clarify relationship with MLP_VISION.md
- **Changes Made** (2025-11-07):
  - Added document status warning at top
  - Fixed API examples to use MLP syntax (`from dioxide import container`)
  - Marked sections 9-14 as "POST-MLP" (async, config, framework integration, production, tooling, patterns)
  - Updated version to 1.2 with changelog
- **Relationship**: Complementary - DX_VISION = aspirational long-term UX, MLP_VISION = concrete near-term spec
- **Priority**: Completed

#### docs/GITHUB_PROJECT_SETUP.md
- **Status**: 🔵 Need to review
- **Content**: GitHub project board setup
- **Action**: **REVIEW** - ensure milestones align with MLP roadmap
- **Priority**: P2

#### docs/SPRINT_READY.md
- **Status**: 🔵 Need to review
- **Content**: Sprint planning process
- **Action**: **REVIEW** - ensure process supports MLP development
- **Priority**: P2

---

## Action Plan

### Phase 1: Critical Updates (This Week)

**Priority 0 - Blocks Progress:**

1. ✅ **Review DX_VISION.md** (COMPLETED 2025-11-07)
   - ✅ Determined: Complementary but outdated
   - ✅ Action taken: Aligned with MLP_VISION.md (see changes above)

2. ✅ **Update STATUS.md** (COMPLETED 2025-11-07)
   - ✅ Changed 0.0.2-alpha scope to "API Realignment"
   - ✅ Updated sprint plan to reflect MLP priorities
   - ✅ Added note about MLP alignment effort

3. ✅ **Rewrite ROADMAP.md** (COMPLETED 2025-11-07)
   - ✅ Created new roadmap matching MLP phase structure
   - ✅ Moved old ROADMAP.md to ROADMAP_OLD.md
   - ✅ All examples use MLP syntax

4. ✅ **Update README.md** (COMPLETED 2025-11-07)
   - ✅ Replaced Quick Start with MLP syntax
   - ✅ Added alpha status warnings throughout
   - ✅ Updated all code examples to use MLP patterns
   - ✅ Added profile system to features list

### Phase 2: Documentation Cleanup (Next Week)

**Priority 1 - Important:**

5. **Update CLAUDE.md** (30 min)
   - Update project instructions to reference MLP
   - Update example commands

6. **Review ADRs** (1 hour)
   - ADR-001: Container architecture
   - ADR-002: PyO3 binding strategy
   - Update or create new ADRs as needed

7. **Review and align DX docs** (1 hour)
   - DEVELOPER_EXPERIENCE.md
   - SPRINT_READY.md
   - GITHUB_PROJECT_SETUP.md

### Phase 3: Historical Records (As Needed)

**Priority 2 - Low urgency:**

8. **Mark historical documents** (30 min total)
   - Add deprecation notices to:
     - 0.0.1-ALPHA_SCOPE.md
     - RELEASE_CHECKLIST_0.0.1-alpha.md
     - Old ROADMAP.md (after v2 created)

---

## Document Hierarchy (Going Forward)

```
Source of Truth:
  └─ docs/MLP_VISION.md (Canonical design)

Strategic Planning:
  └─ ROADMAP_v2.md (Derived from MLP)
  └─ STATUS.md (Current sprint, aligned with MLP)

Implementation Guides:
  └─ README.md (User-facing, MLP syntax)
  └─ CLAUDE.md (Developer-facing, MLP syntax)
  └─ CONTRIBUTING.md (Process, MLP-aware)

Technical Details:
  └─ docs/design/ADR-*.md (Architecture decisions)
  └─ docs/design/*.md (Implementation designs)
  └─ COVERAGE.md (Testing strategy)

Historical:
  └─ ROADMAP.md (deprecated, pre-MLP)
  └─ docs/*-alpha-*.md (deprecated, pre-MLP)
  └─ CHANGELOG.md (historical record)
```

---

## Communication Strategy

### For External Users (if any on Test PyPI):

**Subject**: dioxide API Changes Coming in 0.0.2-alpha

```
Hello dioxide early adopters,

Thank you for trying dioxide v0.0.1-alpha! We're writing to let you know
about significant API changes coming in 0.0.2-alpha as we align with our
canonical MLP (Minimum Loveable Product) vision.

**What's Changing:**
- @component decorator syntax (`@component.factory` instead of `@component(scope=...)`)
- Profile system introduction (@profile.production, @profile.test, etc.)
- Container usage (global singleton pattern)
- Lifecycle protocols for initialization/cleanup

**Timeline:**
- 0.0.2-alpha: Mid-late November 2025
- Migration guide will be provided

**Why:** We're aligning the API with our north star design document to
ensure dioxide becomes the framework we envision.

**What to do:**
- If you're experimenting: Great! Breaking changes are expected in alpha
- If you're building on 0.0.1: Wait for 0.0.2 or be prepared to migrate

Thanks for your patience as we build dioxide the right way!
```

### For GitHub / Public:

**Update README.md with banner:**

```markdown
> **⚠️ ALPHA STATUS**: dioxide is in early alpha. The API is evolving rapidly.
> Breaking changes expected between alpha releases. Not recommended for production use.
> We're aligning with our [MLP Vision](docs/MLP_VISION.md) - expect significant
> API improvements in 0.0.2-alpha (November 2025).
```

---

## Success Criteria

Documentation alignment is complete when:

- [x] All code examples show MLP syntax (DONE 2025-11-07 - Priority 0 complete)
- [x] ROADMAP reflects MLP phase structure (DONE 2025-11-07)
- [x] README quick start uses MLP patterns (DONE 2025-11-07)
- [x] STATUS.md shows MLP-aligned sprint plan (DONE 2025-11-07)
- [ ] Historical docs clearly marked as deprecated (Priority 2)
- [ ] No conflicting information across docs (In progress - Priority 1 next)
- [x] DX_VISION.md reviewed and aligned/merged/deprecated (DONE 2025-11-07)

---

**Next Action**: Update CLAUDE.md with MLP syntax (Priority 1)

**Owner**: Product-Technical Lead
**Timeline**: Phase 1 complete (Nov 7, 2025), Phase 2 starting

**Completed Actions**:
- ✅ DX_VISION.md reviewed and aligned (2025-11-07)
- ✅ STATUS.md updated for MLP realignment (2025-11-07)
- ✅ ROADMAP.md rewritten to reflect MLP phase structure (2025-11-07)
- ✅ README.md updated with MLP syntax (2025-11-07)
- ✅ **ALL PRIORITY 0 TASKS COMPLETE** (2025-11-07)
