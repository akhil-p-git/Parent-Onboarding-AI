"""
Tests for structured logging module.
"""

import json
import logging
from unittest.mock import patch

import pytest

from app.core.logging import (
    DevelopmentFormatter,
    JSONFormatter,
    generate_request_id,
    get_api_key_id,
    get_logger,
    get_request_id,
    get_trace_id,
    get_user_id,
    set_api_key_id,
    set_request_id,
    set_trace_id,
    set_user_id,
)


class TestContextVariables:
    """Tests for context variable functions."""

    def test_request_id_context(self):
        """Test request ID get/set."""
        # Initially None
        set_request_id(None)
        assert get_request_id() is None

        # Set a value
        set_request_id("req-123")
        assert get_request_id() == "req-123"

        # Clear it
        set_request_id(None)
        assert get_request_id() is None

    def test_trace_id_context(self):
        """Test trace ID get/set."""
        set_trace_id(None)
        assert get_trace_id() is None

        set_trace_id("trace-abc")
        assert get_trace_id() == "trace-abc"

        set_trace_id(None)
        assert get_trace_id() is None

    def test_user_id_context(self):
        """Test user ID get/set."""
        set_user_id(None)
        assert get_user_id() is None

        set_user_id("user-456")
        assert get_user_id() == "user-456"

        set_user_id(None)
        assert get_user_id() is None

    def test_api_key_id_context(self):
        """Test API key ID get/set."""
        set_api_key_id(None)
        assert get_api_key_id() is None

        set_api_key_id("key-789")
        assert get_api_key_id() == "key-789"

        set_api_key_id(None)
        assert get_api_key_id() is None

    def test_generate_request_id(self):
        """Test request ID generation."""
        id1 = generate_request_id()
        id2 = generate_request_id()

        # Should be valid UUIDs
        assert len(id1) == 36
        assert len(id2) == 36

        # Should be unique
        assert id1 != id2


class TestJSONFormatter:
    """Tests for JSONFormatter."""

    @pytest.fixture
    def formatter(self):
        """Create a JSONFormatter instance."""
        return JSONFormatter()

    @pytest.fixture
    def log_record(self):
        """Create a sample log record."""
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/app/test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        return record

    def test_basic_format(self, formatter, log_record):
        """Test basic log formatting."""
        result = formatter.format(log_record)
        data = json.loads(result)

        assert data["level"] == "INFO"
        assert data["logger"] == "test.logger"
        assert data["message"] == "Test message"
        assert "timestamp" in data
        assert "service" in data
        assert "version" in data
        assert "environment" in data

    def test_format_with_context(self, formatter, log_record):
        """Test formatting with context variables."""
        set_request_id("req-test-123")
        set_trace_id("trace-test-456")
        set_api_key_id("key-test-789")

        try:
            result = formatter.format(log_record)
            data = json.loads(result)

            assert data["request_id"] == "req-test-123"
            assert data["trace_id"] == "trace-test-456"
            assert data["api_key_id"] == "key-test-789"
        finally:
            set_request_id(None)
            set_trace_id(None)
            set_api_key_id(None)

    def test_format_includes_source(self, formatter, log_record):
        """Test that source location is included."""
        result = formatter.format(log_record)
        data = json.loads(result)

        assert "source" in data
        assert data["source"]["file"] == "test.py"
        assert data["source"]["line"] == 42

    def test_format_with_extra_fields(self, formatter):
        """Test formatting with extra fields."""
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/app/test.py",
            lineno=1,
            msg="Test with extra",
            args=(),
            exc_info=None,
        )
        record.custom_field = "custom_value"
        record.user_count = 42

        result = formatter.format(record)
        data = json.loads(result)

        assert data["custom_field"] == "custom_value"
        assert data["user_count"] == 42

    def test_format_with_exception(self, formatter):
        """Test formatting with exception info."""
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname="/app/test.py",
            lineno=1,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )

        result = formatter.format(record)
        data = json.loads(result)

        assert "exception" in data
        assert data["exception"]["type"] == "ValueError"
        assert data["exception"]["message"] == "Test error"
        assert "traceback" in data["exception"]


class TestDevelopmentFormatter:
    """Tests for DevelopmentFormatter."""

    @pytest.fixture
    def formatter(self):
        """Create a DevelopmentFormatter instance."""
        return DevelopmentFormatter()

    def test_basic_format(self, formatter):
        """Test basic development formatting."""
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/app/test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        assert "INFO" in result
        assert "test.logger" in result
        assert "Test message" in result

    def test_format_with_context(self, formatter):
        """Test development format includes context."""
        set_request_id("req-dev-123")
        set_api_key_id("key-dev-456")

        try:
            record = logging.LogRecord(
                name="test.logger",
                level=logging.INFO,
                pathname="/app/test.py",
                lineno=1,
                msg="Test message",
                args=(),
                exc_info=None,
            )

            result = formatter.format(record)

            # Context should be shown in prefix
            assert "req-dev-1" in result  # First 8 chars
            assert "key-dev-4" in result  # First 8 chars
        finally:
            set_request_id(None)
            set_api_key_id(None)

    def test_color_codes(self, formatter):
        """Test that different levels have different colors."""
        levels = [
            logging.DEBUG,
            logging.INFO,
            logging.WARNING,
            logging.ERROR,
            logging.CRITICAL,
        ]

        results = []
        for level in levels:
            record = logging.LogRecord(
                name="test",
                level=level,
                pathname="/test.py",
                lineno=1,
                msg="Test",
                args=(),
                exc_info=None,
            )
            results.append(formatter.format(record))

        # Each result should be different (due to colors)
        assert len(set(results)) == len(results)


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a Logger instance."""
        logger = get_logger("test.module")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"

    def test_get_logger_same_name_same_instance(self):
        """Test that same name returns same logger."""
        logger1 = get_logger("same.name")
        logger2 = get_logger("same.name")

        assert logger1 is logger2

    def test_get_logger_different_names(self):
        """Test that different names return different loggers."""
        logger1 = get_logger("name.one")
        logger2 = get_logger("name.two")

        assert logger1 is not logger2
        assert logger1.name != logger2.name
