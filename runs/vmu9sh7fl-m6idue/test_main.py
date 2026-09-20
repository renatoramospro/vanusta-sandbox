import subprocess
import sys

def test_execution():
    result = subprocess.run([sys.executable, "main.py"], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        exit(1)
    else:
        exit(0)

if __name__ == "__main__":
    test_execution()