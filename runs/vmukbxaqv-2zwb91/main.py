import hmac
import hashlib
import time

class SecureCellRouter:
    def __init__(self, secret_key: bytes):
        self.secret_key = secret_key
        # Mapeamento seguro de tenant para célula
        self.tenant_cell_map = {
            "tenant-alpha": {"cell": "Cell-A", "fencing_token": 10},
            "tenant-beta": {"cell": "Cell-B", "fencing_token": 5}
        }

    def generate_token(self, tenant_id: str) -> str:
        message = f"{tenant_id}:{time.time()}".encode()
        signature = hmac.new(self.secret_key, message, hashlib.sha256).hexdigest()
        return f"{tenant_id}:{signature}"

    def validate_and_route(self, token: str, target_cell: str, current_fencing_token: int) -> bool:
        try:
            tenant_id, signature = token.split(":")
        except ValueError:
            raise PermissionError("Token malformado ou inválido.")

        if tenant_id not in self.tenant_cell_map:
            raise PermissionError("Tenant não cadastrado.")

        cell_info = self.tenant_cell_map[tenant_id]

        # Validação de Fencing Token para prevenir Split Brain
        if current_fencing_token < cell_info["fencing_token"]:
            raise RuntimeError(f"FENCING REJEITADO: Escritor antigo bloqueado para {tenant_id} na {target_cell}.")

        # Validação de isolamento de célula
        if cell_info["cell"] != target_cell:
            raise PermissionError(f"ACESSO NEGADO: Tenant {tenant_id} não pertence à célula {target_cell} (Tentativa de Tenant Spoofing).")

        return True

def run_security_experiment():
    print("--- INÍCIO DO EXPERIMENTO: Segurança e Validação de Células ---")
    router = SecureCellRouter(secret_key=b"super-secret-control-plane-key")

    # 1. Requisição legítima
    valid_token = router.generate_token("tenant-alpha")
    try:
        router.validate_and_route(valid_token, "Cell-A", current_fencing_token=10)
        print("[Sucesso] Requisição de 'tenant-alpha' permitida na Cell-A.")
    except Exception as e:
        print(f"[Erro Inesperado] {e}")

    # 2. Tentativa de Tenant Spoofing (Acessar Cell-B com token da Cell-A)
    try:
        router.validate_and_route(valid_token, "Cell-B", current_fencing_token=10)
    except PermissionError as err:
        print(f"[CAPTURADO COM SUCESSO - Spoofing]: {err}")

    # 3. Tentativa de Split Brain com Fencing Token desatualizado
    try:
        router.validate_and_route(valid_token, "Cell-A", current_fencing_token=9) # Token menor que 10
    except RuntimeError as err:
        print(f"[CAPTURADO COM SUCESSO - Split Brain]: {err}")

if __name__ == "__main__":
    run_security_experiment()