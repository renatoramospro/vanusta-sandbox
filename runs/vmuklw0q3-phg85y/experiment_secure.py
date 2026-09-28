import os
import time
import threading
import tempfile
import shutil

class SecureSidecar(threading.Thread):
    def __init__(self, config_file_path):
        super().__init__()
        self.config_file_path = config_file_path
        self.running = True
        self.log_level = "INFO"
        self.last_mtime = 0
        self.allowed_levels = {"INFO", "DEBUG", "WARN", "ERROR"}

    def validate_and_parse(self, content):
        """Valida o esquema e os valores permitidos para evitar injeção de configuração."""
        new_config = {}
        lines = content.strip().split("\n")
        for line in lines:
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.split("=", 1)
            if len(parts) != 2:
                raise ValueError(f"Sintaxe de configuração inválida (esperado CHAVE=VALOR): '{line}'")
            key, val = parts[0].strip(), parts[1].strip()
            
            # Validação de esquema estrito
            if key != "LOG_LEVEL":
                raise ValueError(f"Chave de configuração desconhecida ou não permitida: '{key}'")
            if val not in self.allowed_levels:
                raise ValueError(f"Valor inválido para {key}: '{val}'. Permitidos: {self.allowed_levels}")
            
            new_config[key] = val
        return new_config

    def run(self):
        while self.running:
            try:
                if os.path.exists(self.config_file_path):
                    mtime = os.path.getmtime(self.config_file_path)
                    if mtime != self.last_mtime:
                        self.last_mtime = mtime
                        with open(self.config_file_path, "r") as f:
                            content = f.read()
                        
                        # Tenta validar o arquivo de configuração
                        parsed = self.validate_and_parse(content)
                        new_level = parsed.get("LOG_LEVEL")
                        
                        # Aviso de segurança sobre exposição de dados em DEBUG
                        if new_level == "DEBUG" and self.log_level != "DEBUG":
                            print("[SECURITY ALerta] Nível DEBUG ativado. Atenção: logs em DEBUG podem expor dados sensíveis ou segredos!")

                        self.log_level = new_level
                        print(f"[SIDECAR SECURO] Hot-reload aplicado com sucesso. Nível de log atual: {self.log_level}")
            except Exception as e:
                # Fallback seguro: mantém o nível anterior e registra o erro sem quebrar o sidecar
                print(f"[SECURITY ERRO] Falha ao processar nova configuração: {e}. Mantendo fallback seguro (Nível: {self.log_level})")
            
            time.sleep(0.1)

class Application(threading.Thread):
    def __init__(self, request_count=6):
        super().__init__()
        self.request_count = request_count
        self.responses_handled = 0
        self.start_time = time.time()

    def run(self):
        for i in range(1, self.request_count + 1):
            time.sleep(0.2)
            self.responses_handled += 1
            print(f"[APP] Processando requisição de negócio #{i} (Uptime íntegro)")

    def get_uptime(self):
        return time.time() - self.start_time

def atomic_write(file_path, content):
    """Simula atualização atômica usando arquivo temporário + replace."""
    dir_name = os.path.dirname(file_path)
    with tempfile.NamedTemporaryFile('w', dir=dir_name, delete=False) as tf:
        tf.write(content)
        temp_name = tf.name
    os.replace(temp_name, file_path)

def main():
    print("=== INÍCIO DO EXPERIMENTO: Sidecar Pattern com Segurança e Hot-Reload Atômico ===")
    
    tmp_dir = tempfile.mkdtemp()
    config_file = os.path.join(tmp_dir, "config.env")

    # Configuração inicial segura
    atomic_write(config_file, "LOG_LEVEL=INFO\n")

    app = Application(request_count=5)
    app.start()
    
    sidecar = SecureSidecar(config_file)
    sidecar.start()

    time.sleep(0.3)

    print("\n--- TESTE 1: TENTATIVA DE INJEÇÃO / CONFIGURAÇÃO INVÁLIDA (VALOR NÃO PERMITIDO) ---\n")
    atomic_write(config_file, "LOG_LEVEL=HACKED_MODE\n")
    time.sleep(0.3)

    print("\n--- TESTE 2: TENTATIVA DE CONFIGURAÇÃO COM SINTAXE CORROMPIDA ---\n")
    atomic_write(config_file, "INVALID_SYNTAX_WITHOUT_EQUALS\n")
    time.sleep(0.3)

    print("\n--- TESTE 3: ATUALIZAÇÃO VÁLIDA VIA ESCRITA ATÔMICA (INFO -> DEBUG) ---\n")
    atomic_write(config_file, "LOG_LEVEL=DEBUG\n")
    
    app.join()
    sidecar.running = False
    sidecar.join()

    print(f"\n[VALIDAÇÃO] Aplicação principal rodou por {app.get_uptime():.2f} segundos.")
    print(f"[VALIDAÇÃO] Total de requisições tratadas sem reinicialização: {app.responses_handled}")
    print("=== FIM DO EXPERIMENTO COM SUCESSO ===")
    
    shutil.rmtree(tmp_dir)

if __name__ == "__main__":
    main()