import subprocess
import sys

def test_execution():
    # Executa o main.py e captura a saída
    result = subprocess.run([sys.executable, "main.py"], capture_output=True, text=True)
    print(result.stdout)
    
    # Se o código imprimiu "❌ FALHA", o teste deve falhar
    if "❌ FALHA" in result.stdout:
        print("Erro detectado na saída do experimento!")
        sys.exit(1)
    
    # Se houve erro de runtime (stderr não vazio e returncode != 0)
    if result.returncode != 0:
        print(f"Erro de Runtime:\n{result.stderr}")
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    test_execution()