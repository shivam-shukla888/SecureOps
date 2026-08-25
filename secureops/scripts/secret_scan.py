#!/usr/bin/env python3
import os
import re
import sys

SECRET_PATTERNS = [
    (re.compile(r"AIzaSy[A-Za-z0-9_-]{33}"), "Google Gemini API Key"),
    (re.compile(r"gsk_[A-Za-z0-9]{48}"), "Groq API Key"),
    (re.compile(r"-----BEGIN (RSA|EC|OPENSSH|PRIVATE) KEY-----"), "Private Key"),
    (re.compile(r"(?i)(api[_-]?key|secret[_-]?key|password)\s*=\s*['\"](?![A-Za-z0-9_-]*example)(?![A-Za-z0-9_-]*test)[A-Za-z0-9+/=_-]{16,}['\"]"), "Potential Hardcoded Secret"),
]

EXCLUDED_DIRS = {".git", ".pytest_cache", "venv", "__pycache__", "alembic"}
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
                            if pattern.search(line):
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
