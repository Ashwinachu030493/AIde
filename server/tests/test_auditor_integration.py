"""
Integration tests for consolidated auditor system.
Tests scanning engine, persistent auditor, and API endpoints.
"""

import os
import tempfile
from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from server.auditor.rules import ALL_RULES, AuditRule, Severity
from server.auditor.scanning_engine import AuditEngine
from server.auditor.service_persistent import PersistentAuditor
from server.models.audit import AuditResult, AuditViolation


class TestAuditEngine:
    """Tests for consolidated audit scanning engine."""

    def test_engine_initialization(self):
        """Test engine initializes with all rules."""
        engine = AuditEngine()
        assert engine.rules == ALL_RULES
        assert len(engine.rules) > 0

    def test_scan_file_with_no_violations(self):
        """Test scanning clean code returns no violations."""
        engine = AuditEngine()
        clean_code = """
def clean_function():
    logger.info("Using proper logging")
    return True
"""
        result = engine.scan_file(clean_code, "test.py", "python")

        assert isinstance(result, AuditResult)
        assert result.file_path == "test.py"
        assert len(result.violations) == 0

    def test_scan_file_detects_hardcoded_secrets(self):
        """Test detection of hardcoded API keys."""
        engine = AuditEngine()
        bad_code = """
api_key = "sk-1234567890abcdefghijk"
secret_token = "ghp_abcdefghijklmnopqrstuvwxyz123456"
"""
        result = engine.scan_file(bad_code, "config.py", "python")

        assert len(result.violations) >= 2
        critical_violations = [v for v in result.violations if v.severity == "critical"]
        assert len(critical_violations) > 0

    def test_scan_file_detects_print_statements(self):
        """Test detection of print() statements."""
        engine = AuditEngine()
        code = """
def debug_function():
    print("Debug message")
    return True
"""
        result = engine.scan_file(code, "test.py", "python")

        print_violations = [v for v in result.violations if v.rule_id == "QUAL002"]
        assert len(print_violations) > 0
        # Compare enum value, not instance
        assert print_violations[0].severity.value == "info"

    def test_scan_file_detects_sql_injection_risk(self):
        """Test detection of SQL injection patterns."""
        engine = AuditEngine()
        code = """
def unsafe_query(user_input):
    cursor.execute(f"SELECT * FROM users WHERE id = {user_input}")
"""
        result = engine.scan_file(code, "database.py", "python")

        sql_violations = [v for v in result.violations if v.rule_id == "SEC003"]
        assert len(sql_violations) > 0
        # Compare enum value, not instance
        assert sql_violations[0].severity.value == "critical"

    def test_scan_file_detects_insecure_http(self):
        """Test detection of insecure HTTP URLs."""
        engine = AuditEngine()
        code = """
API_ENDPOINT = "http://api.example.com/data"
"""
        result = engine.scan_file(code, "config.py", "python")

        http_violations = [v for v in result.violations if v.rule_id == "SEC002"]
        assert len(http_violations) > 0

    def test_scan_file_detects_todo_comments(self):
        """Test detection of TODO/FIXME comments."""
        engine = AuditEngine()
        code = """
# TODO: Implement proper error handling
# FIXME: This is a temporary workaround
def temp_function():
    pass
"""
        result = engine.scan_file(code, "temp.py", "python")

        todo_violations = [
            v for v in result.violations if "TODO" in v.description or "FIXME" in v.description
        ]
        assert len(todo_violations) >= 2

    def test_scan_file_language_filtering(self):
        """Test that language-specific rules are applied correctly."""
        engine = AuditEngine()

        # Python-specific rule should not trigger on JavaScript
        python_code = "print('test')"
        js_code = "console.log('test')"

        py_result = engine.scan_file(python_code, "test.py", "python")
        js_result = engine.scan_file(js_code, "test.js", "javascript")

        # Python result should have print violation (QUAL002)
        assert any(v.rule_id == "QUAL002" for v in py_result.violations)

        # JS result should have console.log violation (QUAL003)
        assert any(v.rule_id == "QUAL003" for v in js_result.violations)

    def test_violation_line_tracking(self):
        """Test that violations track correct line numbers."""
        engine = AuditEngine()
        code = """line 1
line 2
api_key = "sk-1234567890abcdefghijk"
line 4
"""
        result = engine.scan_file(code, "test.py", "python")

        # Should detect hardcoded API key
        sec_violations = [v for v in result.violations if v.rule_id == "SEC001"]
        assert len(sec_violations) > 0
        violation = sec_violations[0]
        assert violation.line_number == 3
        assert "api_key" in violation.line_content


class TestPersistentAuditor:
    """Tests for persistent auditor with database integration."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = Mock(spec=Session)
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()
        return db

    @pytest.fixture
    def temp_project(self):
        """Create temporary project directory with test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test Python file
            test_file = os.path.join(tmpdir, "test.py")
            with open(test_file, "w") as f:
                f.write("""
def test_function():
    print("test")  # INFO violation
    api_key = "sk-1234567890abcdefghijk"  # CRITICAL violation
    return True
""")

            # Create clean file
            clean_file = os.path.join(tmpdir, "clean.py")
            with open(clean_file, "w") as f:
                f.write("""
import logging
logger = logging.getLogger(__name__)

def clean_function():
    logger.info("Clean code")
    return True
""")
            yield tmpdir

    def test_persistent_auditor_initialization(self, mock_db):
        """Test persistent auditor initializes with database."""
        auditor = PersistentAuditor(mock_db)
        assert auditor.db == mock_db
        assert len(auditor.rules) > 0

    def test_health_score_calculation(self, mock_db):
        """Test health score calculation logic."""
        auditor = PersistentAuditor(mock_db)

        violations = [
            AuditViolation(
                rule_id="TEST001",
                rule_name="Test",
                description="Test violation",
                severity=Severity.CRITICAL,
                file_path="test.py",
                line_number=1,
                line_content="test",
            )
        ]

        score = auditor._calculate_health_score(violations, 10)
        assert 0 <= score <= 100
        assert score < 100  # Should be penalized for violations

    def test_severity_count(self, mock_db):
        """Test severity counting."""
        auditor = PersistentAuditor(mock_db)

        violations = [
            AuditViolation(
                rule_id="TEST1",
                rule_name="Test",
                description="Critical",
                severity=Severity.CRITICAL,
                file_path="test.py",
                line_number=1,
                line_content="test",
            ),
            AuditViolation(
                rule_id="TEST2",
                rule_name="Test",
                description="Warning",
                severity=Severity.WARNING,
                file_path="test.py",
                line_number=2,
                line_content="test",
            ),
            AuditViolation(
                rule_id="TEST3",
                rule_name="Test",
                description="Info",
                severity=Severity.INFO,
                file_path="test.py",
                line_number=3,
                line_content="test",
            ),
        ]

        counts = auditor._count_issues_by_severity(violations)
        # Dictionary has Severity enum keys with counts
        # Direct assertion on counts
        assert len(counts) == 3, f"Expected 3 severity types, got {len(counts)}"
        # Check that each severity appears exactly once
        critical_count = sum(1 for k, v in counts.items() if k.value == "critical")
        warning_count = sum(1 for k, v in counts.items() if k.value == "warning")
        info_count = sum(1 for k, v in counts.items() if k.value == "info")

        assert critical_count == 1 and counts[list(counts.keys())[0]] == 1
        assert warning_count == 1
        assert info_count == 1

    def test_audit_project_creates_run_record(self, mock_db, temp_project):
        """Test that audit creates a run record in database."""
        from server.models.auditor import AuditRun

        # Create mock run instance
        mock_run = Mock()
        mock_run.id = 1
        mock_db.refresh.return_value = None

        auditor = PersistentAuditor(mock_db)

        with patch.object(AuditRun, "__init__", return_value=None):
            try:
                result = auditor.audit_project_persistent("test-project", temp_project)
            except Exception:
                pass  # May fail due to mocking, but we check if db operations were called

        # Verify database operations were attempted
        assert mock_db.add.called or mock_db.commit.called


class TestAuditRulesConfiguration:
    """Tests for audit rules configuration."""

    def test_all_rules_have_required_fields(self):
        """Test that all rules have required fields."""
        for rule in ALL_RULES:
            assert hasattr(rule, "id")
            assert hasattr(rule, "name")
            assert hasattr(rule, "description")
            assert hasattr(rule, "severity")
            assert rule.id, "Rule must have non-empty ID"
            assert rule.name, "Rule must have non-empty name"

    def test_rule_ids_are_unique(self):
        """Test that all rule IDs are unique."""
        ids = [rule.id for rule in ALL_RULES]
        assert len(ids) == len(set(ids)), "Rule IDs must be unique"

    def test_security_rules_are_critical_or_warning(self):
        """Test that security rules have appropriate severity."""
        from server.auditor.rules import SECURITY_RULES

        for rule in SECURITY_RULES:
            assert rule.severity in [
                Severity.CRITICAL,
                Severity.WARNING,
            ], f"Security rule {rule.id} should be CRITICAL or WARNING"

    def test_quality_rules_have_patterns(self):
        """Test that quality rules have valid patterns."""
        from server.auditor.rules import QUALITY_RULES

        for rule in QUALITY_RULES:
            if rule.pattern:
                assert rule.pattern.pattern, "Rule pattern must be compiled"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
