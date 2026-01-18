# ✅ EXECUTION CHECKLIST: v0.3.0 Release Sprint

**Sprint Duration:** Jan 18-22, 2026 (5 days)  
**Goal:** Release AIde v0.3.0 for personal use  
**Status:** ⏳ IN PROGRESS  

---

## 📅 Day 1-2: CI/CD Diagnostics

**Objective:** Identify actual CI/CD failures (not hypotheticals)

### **Day 1 Tasks**
- [ ] Open GitHub Actions: https://github.com/Ashwinachu030493/AIde/actions
- [ ] Find latest failed run (commit 8362124)
- [ ] Check if GitHub CLI available: `gh --version`
  - [ ] YES → Download logs with: `gh run download <RUN_ID>`
  - [ ] NO → Download artifacts manually from web interface
- [ ] Extract and review artifacts:
  - [ ] pytest-logs/test-backend.txt
  - [ ] lint-output.txt
  - [ ] bandit-report.txt
- [ ] **Create:** `CI_DIAGNOSTIC_REPORT.md` with actual errors found
  - [ ] List specific files with lint errors (E501, F401, etc)
  - [ ] List specific test failures (if any)
  - [ ] List actual bandit warnings (filter out B101, B108 - test-only)

**Expected Output:** Clear list of what needs fixing

### **Day 2 Tasks**
- [ ] Reproduce errors locally (fallback verification)
  - [ ] Run: `cd server && flake8 . --statistics`
  - [ ] Run: `bandit -r . -ll`
  - [ ] Run: `pytest tests/ -v --tb=short`
- [ ] Verify findings match GitHub Actions report
- [ ] Create fix plan: Prioritize by complexity
  - [ ] Quick fixes (1-5 minutes each)
  - [ ] Medium fixes (5-20 minutes)
  - [ ] Complex fixes (>20 minutes)
- [ ] **Decision point:** Are fixes achievable in 1 day?
  - [ ] YES → Proceed to Day 3
  - [ ] NO → Extend timeline or escalate complexity

**Expected Output:** Ranked list of fixes to apply

---

## 🔧 Day 3: Apply Fixes

**Objective:** Fix actual errors identified in Days 1-2

### **Quick Fixes (E501 line length)**
- [ ] Identify files with E501 errors
- [ ] Split long lines across multiple statements
- [ ] Example:
  ```python
  # Before
  result = db.query(Model).filter(condition).order_by(sort).limit(10).all()
  
  # After
  result = (
      db.query(Model)
      .filter(condition)
      .order_by(sort)
      .limit(10)
      .all()
  )
  ```
- [ ] Verify locally: `flake8 <file> --select=E501`

### **Import Cleanup (F401 unused imports)**
- [ ] Identify unused imports
- [ ] Remove them from import statements
- [ ] Example:
  ```python
  # Before
  from server.llm import client, config  # config unused
  
  # After
  from server.llm import client
  ```
- [ ] Verify locally: `flake8 <file> --select=F401`

### **Test Failures (if any)**
- [ ] Identify failing test
- [ ] Check root cause:
  - [ ] Missing fixture?
  - [ ] Database state pollution?
  - [ ] Timeout in ChromaDB?
  - [ ] Environment variable missing?
- [ ] Apply fix
- [ ] Run test locally: `pytest <test_file> -v`

### **Commit All Fixes**
- [ ] Stage all changes: `git add .`
- [ ] Commit with clear message:
  ```bash
  git commit -m "fix(ci): resolve flake8 and test failures
  
  - Fix E501: Line length violations in dashboard/router_simple.py
  - Fix F401: Remove unused imports from test files
  - Fix pytest: Add database cleanup fixture to test_vector_store_integration.py
  - Verify all 46 tests pass locally"
  ```
- [ ] **DO NOT PUSH YET** - Verify all fixes work first

### **Local Verification**
- [ ] Run full lint suite: `flake8 server/ --count --statistics`
  - [ ] Result: 0 errors (or only acceptable warnings)
- [ ] Run bandit: `bandit -r server/ -ll`
  - [ ] Result: Only LOW severity warnings (B101, B108, etc)
- [ ] Run tests: `pytest server/tests/ -v`
  - [ ] Result: 46/46 PASSED
- [ ] **All checks pass?**
  - [ ] YES → Proceed to Day 4 push
  - [ ] NO → Debug and reapply fixes

**Expected Output:** Green checks locally, ready to push

---

## ✅ Day 4: Re-enable Strict CI Checks

**Objective:** Push fixes and verify CI pipeline goes green

### **Update CI Workflow**
- [ ] Edit: `.github/workflows/ci.yml`
- [ ] Find: `continue-on-error: true` for flake8, bandit, codecov
- [ ] Remove those lines (fail on error = good)
- [ ] Example changes:
  ```yaml
  # BEFORE (permissive)
  - name: Lint with flake8
    run: flake8 server/
    continue-on-error: true  # ← REMOVE THIS

  # AFTER (strict)
  - name: Lint with flake8
    run: |
      cd server
      flake8 . --count --show-source --statistics
    # ← NO continue-on-error
  ```

### **Push Changes**
- [ ] Stage workflow changes: `git add .github/workflows/ci.yml`
- [ ] Commit: `git commit -m "fix(ci): re-enable strict checks after fixing errors"`
- [ ] Push: `git push origin main`
- [ ] **Monitor workflow:** Wait 5-10 minutes

### **Verify Green Pipeline**
- [ ] Open: https://github.com/Ashwinachu030493/AIde/actions
- [ ] Check latest run triggered by your push
- [ ] Verify each job:
  - [ ] Lint Backend: ✅ PASSED
  - [ ] Security Scan: ✅ PASSED (or only LOW warnings)
  - [ ] Test Backend (3.11): ✅ PASSED (46 tests)
  - [ ] Test Backend (3.12): ✅ PASSED (46 tests)
  - [ ] Frontend Build: ✅ PASSED
- [ ] **If any red X:** Go back, debug, reapply fixes

**Expected Output:** All green checkmarks on GitHub Actions

---

## 📦 Day 5: Release Preparation

**Objective:** Create v0.3.0 release with proper tagging and packaging

### **Version Alignment**
- [ ] Current backend version (check): `server/main_enhanced.py` line ~30
  - [ ] Expected: `version="0.3.0"` ✅
  - [ ] If different: Update it
- [ ] Current extension version: `extension/package.json`
  - [ ] Expected: `"version": "0.3.0"`
  - [ ] If different: Update with: `cd extension && npm version 0.3.0 --no-git-tag-version`
- [ ] Current changelog version: `CHANGELOG.md` line 1
  - [ ] Expected: `## [0.3.0]`
  - [ ] If different: Update with: `sed -i 's/\[1.0.0\]/[0.3.0]/' CHANGELOG.md`
- [ ] Commit version alignment:
  ```bash
  git add extension/package.json CHANGELOG.md server/main_enhanced.py
  git commit -m "chore(release): align all versions to v0.3.0"
  git push origin main
  ```

### **Create Release Tag**
- [ ] Create annotated tag with release notes:
  ```bash
  git tag v0.3.0 -m "Release v0.3.0: Personal Use Release
  
  ## Features
  - AI Chat: Multi-provider LLM support (OpenAI, Anthropic, Groq, HuggingFace)
  - Document Ingestion: Semantic code search with ChromaDB
  - Code Auditor: Quality checks with persistent results
  - Dashboard: Project health metrics and activity timeline
  - VS Code Extension: Native integration with tabbed interface
  
  ## Performance
  - 500x faster startup: 10 minutes → 2 seconds
  - Lazy vector store initialization
  - Timeout-protected embedding loads
  
  ## Quality
  - 46/46 tests passing
  - Clean modular architecture
  - Comprehensive failover mechanisms
  
  ## Scope
  This release is optimized for personal use (localhost, single user).
  See documentation for team deployment options (v0.3.1+)."
  ```
- [ ] Push tag: `git push origin v0.3.0`
- [ ] Verify on GitHub: https://github.com/Ashwinachu030493/AIde/releases
  - [ ] Tag created ✅
  - [ ] Release notes visible ✅

### **Build Extension VSIX**
- [ ] Navigate to extension: `cd extension`
- [ ] Install dependencies: `npm install`
- [ ] Compile TypeScript: `npm run compile`
- [ ] Package VSIX: `vsce package`
  - [ ] Expected file: `aide-vscode-0.3.0.vsix`
  - [ ] Expected size: ~5-10 MB
- [ ] Verify VSIX contents:
  ```bash
  unzip -l aide-vscode-0.3.0.vsix | head -30
  # Should show: extension.js, webview files, package.json, etc.
  ```

### **Create GitHub Release (Manual)**
- [ ] Navigate to: https://github.com/Ashwinachu030493/AIde/releases
- [ ] Click: **Draft a new release**
- [ ] Fill in:
  - [ ] Tag: `v0.3.0`
  - [ ] Title: `AIde v0.3.0 - Personal Use Release`
  - [ ] Description: (paste from above release notes)
  - [ ] Attach file: Drag `aide-vscode-0.3.0.vsix`
- [ ] Click: **Publish release** 🎉

**Expected Output:** Live release on GitHub + VSIX available for download

---

## 🎯 Personal Use Validation (All 16 Items)

**Before closing sprint, verify ALL:**

### **Technical (5 items)**
- [ ] CI/CD pipeline: All jobs green (screenshot: https://github.com/Ashwinachu030493/AIde/actions)
- [ ] Tests: 46/46 passing (log file proof)
- [ ] Versions: v0.3.0 everywhere
  - [ ] `extension/package.json`
  - [ ] `server/main_enhanced.py`
  - [ ] `CHANGELOG.md`
- [ ] Server startup: <5 seconds
  - [ ] Run: `time python server/main_enhanced.py`
  - [ ] Check: Real user time < 5s
- [ ] Health check: Returns 200 OK
  - [ ] Run in another terminal: `curl http://localhost:8000/health/detailed`
  - [ ] Verify: `{"status": "healthy"}`

### **Extension (3 items)**
- [ ] VSIX builds without errors
  - [ ] File exists: `aide-vscode-0.3.0.vsix`
  - [ ] File size: >1 MB (not corrupted)
- [ ] Extension installs in VS Code
  - [ ] Open VS Code
  - [ ] Extensions → Install from VSIX
  - [ ] Select VSIX file
  - [ ] Verify: Shows "Installed"
- [ ] Extension activates without console errors
  - [ ] Open Dev Tools: Ctrl+Shift+J
  - [ ] Check Console tab: No red errors
  - [ ] Click AIde icon: Sidebar opens cleanly

### **Functional (3 items)**
- [ ] Chat works with API key
  - [ ] Open Settings panel
  - [ ] Add OpenAI API key (test provider)
  - [ ] Write test message in Chat
  - [ ] Verify: Response appears without errors
- [ ] Document ingestion processes files
  - [ ] Upload sample Python file via Chat
  - [ ] Wait: ChromaDB indexing completes
  - [ ] Verify: File appears in "Indexed Files" list
- [ ] Dashboard loads project overview
  - [ ] Click Dashboard tab
  - [ ] Verify: Shows health score, file count, activity chart
  - [ ] No red error messages

### **Documentation (3 items)**
- [ ] README updated with clear install instructions
  - [ ] Covers: Requirements, Installation, Configuration
  - [ ] Has: Screenshots or step-by-step guide
  - [ ] Works: Follow it, extension installs
- [ ] Troubleshooting section addresses common errors
  - [ ] Covers: API key errors, server not running, ChromaDB timeout
  - [ ] Each error has: Solution with commands
- [ ] Known limitations clearly documented
  - [ ] States: "Localhost only (127.0.0.1:8000)"
  - [ ] States: "Single user (not for teams)"
  - [ ] States: "Manual backups required"

### **Other (2 items)**
- [ ] No critical errors in 1-hour usage session
  - [ ] Use extension normally for 1 hour
  - [ ] Chat with API key
  - [ ] Ingest a document
  - [ ] Run audit on project
  - [ ] Check Dev Tools: No unhandled errors
- [ ] Commit messages clear and descriptive
  - [ ] All fixes have clear messages (not "fix")
  - [ ] Messages explain what was fixed

**Status:** RELEASE READY when 16/16 ✅

---

## 🚀 Release Confirmation

**When all 16 items complete:**

```
✅ PERSONAL USE RELEASE v0.3.0 READY
📦 GitHub Release: https://github.com/Ashwinachu030493/AIde/releases/tag/v0.3.0
📦 Extension VSIX: aide-vscode-0.3.0.vsix
📚 Documentation: README.md + COMPREHENSIVE_AUDIT_REPORT.md
🎯 Timeline: 5 days (Jan 18-22, 2026)

Users can now:
1. Download VSIX from GitHub release
2. Install in VS Code
3. Run backend server (python main_enhanced.py)
4. Use AIde for personal AI-assisted coding
```

---

## 🔄 If Issues Arise

### **If CI Still Fails on Day 4**
- [ ] Read error message carefully
- [ ] Check if error is legitimate or false positive (B101, B108)
- [ ] If legitimate: Go back, fix, re-push
- [ ] If false positive: Add to `.flake8` config:
  ```ini
  [flake8]
  extend-ignore = E501,W503,B101,B108
  ```

### **If Tests Fail After Fix**
- [ ] Run test locally: `pytest <test_name> -v -s`
- [ ] Add debug output to understand failure
- [ ] Check if test setup/teardown is correct
- [ ] Verify no hardcoded paths or environment dependencies

### **If VSIX Won't Build**
- [ ] Check npm errors: `npm run compile` (look at error)
- [ ] Common fixes:
  - [ ] Delete `node_modules` and `package-lock.json`: `rm -r node_modules package-lock.json`
  - [ ] Reinstall: `npm install`
  - [ ] Rebuild: `npm run compile`

### **If Stuck**
- [ ] Document the issue: What did you try? What failed?
- [ ] Create GitHub Issue with:
  - [ ] Error message (full stack trace)
  - [ ] Steps to reproduce
  - [ ] Environment (OS, Node version, VS Code version)
- [ ] Escalate to next sprint (v0.3.1)

---

## 📊 Daily Status Update Template

**Use this template each day to track progress:**

```
## Day X Update (Jan YZ, 2026)

### Completed
- [ ] Task 1
- [ ] Task 2

### In Progress
- Task 3 (60% done)

### Blockers
- None / Issue: ...

### Next Steps
- Tomorrow: ...

### Status
🟢 On track / 🟡 Slightly delayed / 🔴 Blocked
```

---

**🎯 START EXECUTION: Open GitHub Actions and begin Day 1-2 diagnostics**

**Questions?** See IMMEDIATE_ACTIONS.md for detailed command reference
