import subprocess, sys
try:
    result = subprocess.run(
        [sys.executable, "-c", "print('hello from sub')"],
        capture_output=True, text=True, timeout=10
    )
    msg = f"stdout={result.stdout}\nstderr={result.stderr}\nrc={result.returncode}"
except Exception as e:
    msg = f"ERROR: {e}"
with open("_simple_out.txt", "w") as f:
    f.write(msg)