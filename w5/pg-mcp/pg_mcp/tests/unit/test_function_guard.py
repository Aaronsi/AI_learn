"""Unit tests for function guard"""

import pytest
from sqlglot import parse_one
from pg_mcp.security.function_guard import FunctionGuard


def test_default_safe_functions():
    """Test default safe functions are allowed"""
    guard = FunctionGuard()
    
    stmt = parse_one("SELECT count(*) FROM users")
    violations = guard.validate_functions(stmt)
    assert len(violations) == 0
    
    stmt = parse_one("SELECT lower(name) FROM users")
    violations = guard.validate_functions(stmt)
    assert len(violations) == 0


def test_custom_allowed_functions():
    """Test custom allowed functions"""
    guard = FunctionGuard(allowed_functions=["custom_func", "my_func"])
    
    stmt = parse_one("SELECT custom_func(id) FROM users")
    violations = guard.validate_functions(stmt)
    assert len(violations) == 0
    
    stmt = parse_one("SELECT my_func(id) FROM users")
    violations = guard.validate_functions(stmt)
    assert len(violations) == 0


def test_unknown_function():
    """Test unknown function is rejected"""
    guard = FunctionGuard()
    
    stmt = parse_one("SELECT unknown_func(id) FROM users")
    violations = guard.validate_functions(stmt)
    assert len(violations) > 0
    assert any("unknown_func" in v for v in violations)


def test_multiple_functions():
    """Test multiple functions in query"""
    guard = FunctionGuard()
    
    stmt = parse_one("SELECT count(*), sum(amount), avg(price) FROM orders")
    violations = guard.validate_functions(stmt)
    assert len(violations) == 0

