"""Unit tests for sanitizer"""

from pg_mcp.security.sanitizer import Sanitizer


def test_sensitive_column_detection():
    """Test sensitive column name detection"""
    sanitizer = Sanitizer(["password", "secret", "token"])
    
    assert sanitizer.is_sensitive_column("password") is True
    assert sanitizer.is_sensitive_column("user_password") is True
    assert sanitizer.is_sensitive_column("secret_key") is True
    assert sanitizer.is_sensitive_column("name") is False
    assert sanitizer.is_sensitive_column("email") is False


def test_sanitize_for_llm():
    """Test sanitization for LLM"""
    sanitizer = Sanitizer(["password", "secret"])
    
    columns = ["id", "name", "password", "email", "secret_key"]
    rows = [
        {"id": 1, "name": "Alice", "password": "secret123", "email": "alice@example.com", "secret_key": "key123"},
        {"id": 2, "name": "Bob", "password": "secret456", "email": "bob@example.com", "secret_key": "key456"},
    ]
    
    safe_cols, safe_rows = sanitizer.sanitize_for_llm(columns, rows, max_rows=2, max_cols=10)
    
    assert "password" not in safe_cols
    assert "secret_key" not in safe_cols
    assert "id" in safe_cols
    assert "name" in safe_cols
    assert "email" in safe_cols
    
    assert len(safe_rows) == 2
    assert "password" not in safe_rows[0]
    assert "secret_key" not in safe_rows[0]


def test_sanitize_row_limit():
    """Test row limit in sanitization"""
    sanitizer = Sanitizer([])
    
    columns = ["id", "name"]
    rows = [{"id": i, "name": f"User{i}"} for i in range(30)]
    
    safe_cols, safe_rows = sanitizer.sanitize_for_llm(columns, rows, max_rows=20, max_cols=10)
    
    assert len(safe_rows) == 20


def test_sanitize_col_limit():
    """Test column limit in sanitization"""
    sanitizer = Sanitizer([])
    
    columns = [f"col{i}" for i in range(15)]
    rows = [dict(zip(columns, range(15)))]
    
    safe_cols, safe_rows = sanitizer.sanitize_for_llm(columns, rows, max_rows=10, max_cols=10)
    
    assert len(safe_cols) == 10


def test_generate_summary():
    """Test summary generation"""
    sanitizer = Sanitizer(["password"])
    
    columns = ["id", "age", "name", "password"]
    rows = [
        {"id": 1, "age": 25, "name": "Alice", "password": "secret"},
        {"id": 2, "age": 30, "name": "Bob", "password": "secret"},
        {"id": 3, "age": 28, "name": "Charlie", "password": "secret"},
    ]
    
    summary = sanitizer.generate_summary(columns, rows, total_count=3)
    
    assert summary["total_rows"] == 3
    assert summary["sample_rows"] == 3
    assert "password" not in summary["column_stats"]
    assert "id" in summary["column_stats"]
    assert "age" in summary["column_stats"]
    
    # Check numeric stats
    age_stats = summary["column_stats"]["age"]
    assert "min" in age_stats
    assert "max" in age_stats
    assert "avg" in age_stats
    
    # Check string stats
    name_stats = summary["column_stats"]["name"]
    assert "unique_count" in name_stats

