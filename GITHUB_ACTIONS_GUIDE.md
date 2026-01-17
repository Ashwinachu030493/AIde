# GitHub Actions Quick Reference

## CI Pipeline (.github/workflows/ci.yml)

### Triggers
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Manual dispatch via GitHub UI

### Jobs Overview

| Job | Purpose | Duration |
|-----|---------|----------|
| test-backend | Run Python tests on 3.11, 3.12 | ~3-5 min |
| test-frontend | TypeScript compile + lint | ~2-3 min |
| lint-backend | Code quality checks | ~1-2 min |
| security-scan | Vulnerability scanning | ~2-3 min |
| integration-tests | Full test suite + PostgreSQL | ~5-7 min |
| build-summary | Aggregate results | ~10 sec |

### Total Pipeline Duration: ~10-15 minutes

### Required Secrets (Optional)
- `CODECOV_TOKEN` - For code coverage reporting (codecov.io)

---

## CD Pipeline (.github/workflows/cd.yml)

### Triggers
- Git tags matching `v*.*.*` (e.g., v0.3.0, v1.0.0)
- Manual dispatch with environment selection

### Deployment Flow

```
Tag Push (v0.3.0)
    ↓
build-and-publish
    ↓
├─→ deploy-staging (if manual dispatch to staging)
└─→ deploy-production (if tag push or manual to prod)
```

### Manual Deployment
1. Go to Actions tab in GitHub
2. Select "CD Pipeline" workflow
3. Click "Run workflow"
4. Choose environment: staging or production
5. Click "Run workflow"

### Required Secrets (Production)
- Deployment credentials (server SSH keys, etc.)
- Configure in GitHub Settings → Secrets and variables → Actions

---

## Release Workflow (.github/workflows/release.yml)

### Triggers
- Git tags matching `v*.*.*`

### Automated Actions
1. Generate changelog from git history
2. Update CHANGELOG.md
3. Bump version in files
4. Build Docker images
5. Tag Docker images with version

### Version Format
- Follows Semantic Versioning (semver.org)
- Format: `vMAJOR.MINOR.PATCH`
- Examples: v0.3.0, v1.0.0, v1.2.3

---

## Local Development

### Run Tests Locally
```bash
# Backend tests
cd server
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=. --cov-report=html

# Specific test file
pytest tests/test_llm_client_integration.py -v
```

### Run Linters Locally
```bash
# Python linting
cd server
flake8 .
black --check .
isort --check-only .

# TypeScript
cd extension
npm run lint
npm run compile
```

### Run Security Scans Locally
```bash
# Install tools
pip install bandit safety

# Run scans
cd server
bandit -r . -ll
safety check
```

---

## Workflow Status Badges

Add to README.md:

```markdown
![CI Pipeline](https://github.com/YOUR_USERNAME/AIde/workflows/CI%20Pipeline/badge.svg)
![CD Pipeline](https://github.com/YOUR_USERNAME/AIde/workflows/CD%20Pipeline/badge.svg)
```

---

## Common Tasks

### Creating a Release

```bash
# 1. Update version numbers
# (Automated by release workflow)

# 2. Commit changes
git add .
git commit -m "chore: prepare release v0.3.0"

# 3. Create and push tag
git tag -a v0.3.0 -m "Release v0.3.0"
git push origin main --tags

# 4. CI/CD automatically:
#    - Runs all tests
#    - Generates changelog
#    - Builds artifacts
#    - Creates GitHub release
#    - Deploys to production
```

### Hotfix Deployment

```bash
# 1. Create hotfix branch
git checkout -b hotfix/critical-fix

# 2. Make fix and commit
git commit -m "fix: critical issue"

# 3. Merge to main
git checkout main
git merge hotfix/critical-fix

# 4. Tag and push
git tag -a v0.3.1 -m "Hotfix v0.3.1"
git push origin main --tags
```

### Rollback Deployment

```bash
# 1. Find previous working tag
git tag -l

# 2. Checkout previous version
git checkout v0.2.9

# 3. Create rollback tag
git tag -a v0.3.1-rollback -m "Rollback to v0.2.9"

# 4. Push tag to trigger deployment
git push origin v0.3.1-rollback
```

---

## Troubleshooting

### Pipeline Failures

#### Test Failures
1. Check test logs in GitHub Actions
2. Run tests locally: `pytest server/tests/ -v`
3. Fix issues
4. Commit and push

#### Lint Failures
1. Run linters locally: `flake8 server/`
2. Auto-fix with: `black server/` and `isort server/`
3. Commit and push

#### Security Scan Failures
1. Review Bandit/Safety reports
2. Update vulnerable dependencies: `pip install --upgrade`
3. Fix security issues
4. Commit and push

### Deployment Failures

#### Staging Deployment Failed
1. Check CD workflow logs
2. Verify staging server accessibility
3. Check deployment credentials in GitHub Secrets
4. Retry deployment

#### Production Deployment Failed
1. **DO NOT PANIC** - Previous version still running
2. Check CD workflow logs
3. If critical, perform rollback (see above)
4. Fix issue in new branch
5. Test thoroughly
6. Create new release tag

---

## CI/CD Best Practices

### Before Pushing
```bash
# Run full test suite
pytest server/tests/ -v

# Run linters
black server/
isort server/
flake8 server/

# Test TypeScript compilation
cd extension
npm run compile
```

### Commit Messages
Follow Conventional Commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `test:` - Test updates
- `chore:` - Maintenance
- `refactor:` - Code refactoring

Examples:
```
feat: add user authentication
fix: resolve SQL injection vulnerability
test: add integration tests for LLM client
docs: update API documentation
```

### Pull Request Workflow
1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes and commit
3. Push branch: `git push origin feature/my-feature`
4. Create PR on GitHub
5. CI runs automatically
6. Fix any failures
7. Get review approval
8. Merge to main

---

## Monitoring

### GitHub Actions Dashboard
- Navigate to repository → Actions tab
- View all workflow runs
- Click run for detailed logs
- Download artifacts (build outputs)

### Key Metrics to Monitor
- Test pass rate (target: 100%)
- Pipeline duration (target: <15 min)
- Security scan results (target: 0 high/critical)
- Code coverage (target: >80%)

---

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [pytest Documentation](https://docs.pytest.org/)
- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
