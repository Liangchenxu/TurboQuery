import subprocess, sys, os
os.chdir(r"d:\tqtq\TurboQuery")
r = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/test_basic.py", "-v", "--tb=long"],
    capture_output=True, text=True
)
with open("_test_result.txt", "w", encoding="utf-8") as f:
    f.write("=== STDOUT ===\n")
    f.write(r.stdout)
    f.write("\n=== STDERR ===\n")
    f.write(r.stderr)
    f.write(f"\n=== RETURN CODE: {r.returncode} ===\n")
print("Done. Check _test_result.txt")