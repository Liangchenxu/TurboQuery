import subprocess, sys, os, shutil
os.chdir(r"d:\tqtq\TurboQuery")

# Clear pycache
for root, dirs, files in os.walk("."):
    for d in dirs:
        if d == "__pycache__":
            shutil.rmtree(os.path.join(root, d), ignore_errors=True)

result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/test_basic.py", "-v", "--tb=long", "-p", "no:cacheprovider"],
    capture_output=True, text=True, timeout=120
)
out = f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}\n\nRC: {result.returncode}"
with open(r"d:\tqtq\TurboQuery\pytest_result.txt", "w", encoding="utf-8") as f:
    f.write(out)