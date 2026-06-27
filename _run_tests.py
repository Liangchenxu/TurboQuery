"""Run tests and print output."""
import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/test_basic.py", "-v", "--tb=short"],
    cwd="d:/tqtq/TurboQuery",
    capture_output=True,
    text=True,
)
print("STDOUT:")
print(result.stdout)
print("STDERR:")
print(result.stderr)
print(f"Return code: {result.returncode}")