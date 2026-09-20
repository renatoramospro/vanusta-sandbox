import subprocess
import sys

def run():
    print("Iniciando execução dos testes com pytest...")
    result = subprocess.run([sys.executable, "-m", "pytest", "test_dispatcher.py"], capture_output=False)
    if result.returncode == 0:
        print("\n✅ TODOS OS TESTES PASSARAM!")
    else:
        print("\n❌ TESTES FALHARAM!")
        sys.exit(result.returncode)

if __name__ == "__main__":
    run()