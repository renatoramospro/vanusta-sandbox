import os
import time
import threading
import tempfile
import shutil

class Application(threading.Thread):
    """Simula a aplicação principal de negócio."""
    def __init__(self, request_count=5):
        super().__init__()
        self.request_count = request_count
        self.running = True
        self.uptime_start = time.time()
        self.responses_handled = 0

    def run(self):
        while self.running and self.responses_handled < self.request_count:
            time.sleep(0.2)
            self.responses_handled += 1
            print(f"[APP] Processando requisição de negócio #{self.responses_handled}")

    def get_uptime(self):
        return time.time() - self.uptime_start

class Sidecar(threading.Thread):
    """Simula o container Sidecar responsável por preocupações transversais (ex: Logging/Config dinâmica)."""
    def __init__(self, config_path):
        super().__init__()
        self.config_path = config_path
        self.running = True
        self.current_log_level = self._read_config()

    def _read_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                content = f.read().strip()
                # Exemplo de formato: LOG_LEVEL=INFO
                for line in content.splitlines():
                    if line.startswith("LOG_LEVEL="):
                        return line.split("=")[1]
        return "INFO"

    def run(self):
        while self.running:
            # Simula hot-reload lendo a configuração periodicamente
            new_level = self._read_config()
            if new_level != self.current_log_level:
                print(f"[SIDECAR] Hot-reload detectado! Nível de log alterado de {self.current_log_level} para {new_level}")
                self.current_log_level = new_level
            
            print(f"[SIDECAR] Coletando métricas/logs (Nível atual: {self.current_log_level})")
            time.sleep(0.3)

def main():
    print("=== INÍCIO DO EXPERIMENTO: Sidecar Pattern com Hot-Reload ===" )
    
    # Cria um diretório temporário simulando um volume compartilhado (ex: Kubernetes ConfigMap volume)
    tmp_dir = tempfile.mkdtemp()
    config_file = os.path.join(tmp_dir, "sidecar_config.env")
    
    # Configuração inicial
    with open(config_file, "w") as f:
        f.write("LOG_LEVEL=INFO\n")

    # Inicia a aplicação principal
    app = Application(request_count=8)
    app.start()
    
    # Inicia o sidecar apontando para o arquivo de configuração compartilhado
    sidecar = Sidecar(config_file)
    sidecar.start()

    # Deixa rodar por um instante com LOG_LEVEL=INFO
    time.sleep(0.6)

    print("\n--- ATUALIZANDO CONFIGURAÇÃO DO SIDECAR EM TEMPO REAL (SEM REINICIAR A APLICAÇÃO) ---\n")
    # Atualiza a configuração no volume compartilhado
    with open(config_file, "w") as f:
        f.write("LOG_LEVEL=DEBUG\n")

    # Aguarda o término do processamento da aplicação
    app.join()
    
    # Encerra o sidecar
    sidecar.running = False
    sidecar.join()

    print(f"\n[VALIDAÇÃO] Aplicação principal rodou por {app.get_uptime():.2f} segundos.")
    print(f"[VALIDAÇÃO] Total de requisições tratadas sem reinicialização: {app.responses_handled}")
    print("=== FIM DO EXPERIMENTO COM SUCESSO ===")
    
    # Limpeza do diretório temporário
    shutil.rmtree(tmp_dir)

if __name__ == "__main__":
    main()