#!/usr/bin/env python3
import os
import re
import sys

# Explicit safe test fixtures (must be exact matches, not blanket "test" matching)
SAFE_TEST_FIXTURES = {
    "test-secret-api-key-12345",
    "test-hmac-secret-key-12345",
    "your-secure-bearer-api-key-here",
    "your-gemini-api-key-here",
    "your-groq-api-key-here",
    "your-primary-api-key-here",
    "your-hmac-sha256-secret-key-here",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/secureops",
    "postgresql+asyncpg://postgres:postgres@postgres:5432/secureops",
    "postgresql+asyncpg://user:pass@localhost:5432/db",
    "postgresql+asyncpg://invalid_user:invalid_pass@127.0.0.1:5439/nonexistent_db",
    "postgresql://user:pass@supabase-host.com:5432/postgres",
    "postgres://user:pass@supabase-host.com:5432/postgres",
    "postgresql+asyncpg://user:pass@supabase-host.com:5432/postgres",
}

SECRET_PATTERNS = [
    (re.compile(r"AIzaSy[A-Za-z0-9_-]{33}"), "Google Gemini API Key"),
    (re.compile(r"gsk_[A-Za-z0-9]{48}"), "Groq API Key"),
    (re.compile(r"sk-[A-Za-z0-9]{32,48}"), "OpenAI API Key"),
    (re.compile(r"secops_live_[A-Za-z0-9_-]{32,}"), "SecOps Live API Key"),
    (re.compile(r"hmac_sec_[A-Za-z0-9_-]{32,}"), "Hardcoded HMAC Secret"),
    (re.compile(r"-----BEGIN (RSA|EC|OPENSSH|PRIVATE) KEY-----"), "Private Key"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS Access Key ID"),
    (re.compile(r"ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{50,}"), "GitHub Personal Access Token"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9_-]{10,60}"), "Slack API Token"),
    (re.compile(r"sk_live_[0-9a-zA-Z]{24,}"), "Stripe Live Secret Key"),
    (re.compile(r"postgres(?:ql)?(?:\+[a-z0-9]+)?://[^:]+:[^@\s'\"]+@[^/]+/[^\s'\"]+"), "Database URL containing embedded password"),
    (re.compile(r"(?i)(api[_-]?key|secret[_-]?key|password)\s*=\s*['\"]([A-Za-z0-9+/=_-]{16,})['\"]"), "Potential Hardcoded Secret"),
]

EXCLUDED_DIRS = {".git", ".pytest_cache", "venv", ".venv", "__pycache__", "node_modules", "dist", "alembic"}
EXCLUDED_FILES = {".env", ".env.example", "secret_scan.py"}


def scan_repository(root_dir: str) -> bool:
    found_issues = False
    print(f"Scanning directory '{root_dir}' for hardcoded secrets...")

    for current_root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

        for file_name in files:
            if file_name in EXCLUDED_FILES or file_name.endswith(".pyc"):
                continue

            file_path = os.path.join(current_root, file_name)
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        for pattern, desc in SECRET_PATTERNS:
                            match = pattern.search(line)
                            if match:
                                matched_val = match.group(0)
                                # Check if matched string or inner captured group is a known safe test fixture
                                if matched_val in SAFE_TEST_FIXTURES:
                                    continue
                                if match.groups() and match.group(len(match.groups())) in SAFE_TEST_FIXTURES:
                                    continue

                                print(f"[SECRET DETECTED] {file_path}:{line_num} -> {desc}")
                                found_issues = True
            except Exception as e:
                pass

    if not found_issues:
        print("[SUCCESS] Secret Scan Passed: No hardcoded API keys or secrets detected.")
    else:
        print("[FAILED] Secret Scan Failed: Secrets detected in repository!")

    return not found_issues


if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    success = scan_repository(base_dir)
    sys.exit(0 if success else 1)
