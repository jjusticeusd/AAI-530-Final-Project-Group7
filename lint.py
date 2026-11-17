import subprocess
import sys

ruff = [sys.executable, "-m", "ruff"]
check = subprocess.run([*ruff, "check", "--fix"])
subprocess.run([*ruff, "format"])
sys.exit(check.returncode)
