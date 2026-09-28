import sys

# --- Sistemas Legado e Novo (Microsserviço) ---

class LegacyMonolith:
    def get_user_profile(self, user_id: int) -> dict:
        # Sistema antigo operando no banco monolítico
        return {"id": user_id, "name": f"User {user_id}", "source": "monolith", "version": "legacy"}

class ModernMicroservice:
    def get_user_profile(self, user_id: int) -> dict:
        # Novo sistema operando no banco isolado do domínio
        return {"id": user_id, "name": f"User {user_id}", "source": "microservice", "version": "v1"}

# --- Strangler Fig Facade (Proxy com Roteamento e Feature Toggle) ---

class StranglerFacade:
    def __init__(self, monolith: LegacyMonolith, microservice: ModernMicroservice):
        self.monolith = monolith
        self.microservice = microservice
        # Feature toggle simulando liberação gradual (ex: lista de IDs migrados ou percentual)
        self.migrated_users = {1, 2, 3}  # Usuários cujos dados já foram migrados para o novo domínio

    def get_profile(self, user_id: int) -> dict:
        """
        Estratégia de Roteamento:
        - Se o usuário estiver na base de dados migrada, direciona para o microsserviço.
        - Caso contrário, mantém no monolito (Strangler Fig pattern).
        - Inclui fallback de segurança em caso de falha no microsserviço (Zero Downtime).
        """
        try:
            if user_id in self.migrated_users:
                # Roteamento para o novo microsserviço
                return self.microservice.get_user_profile(user_id)
            else:
                # Roteamento para o monolito legado
                return self.monolith.get_user_profile(user_id)
        except Exception as e:
            # Mecanismo de contingência / Fallback para garantir continuidade do negócio
            print(f"[AVISO] Falha no microsserviço para user {user_id}. Executando fallback para o monolito. Erro: {e}")
            return self.monolith.get_user_profile(user_id)

# --- Execução do Experimento e Validação ---

def run_experiment():
    monolith = LegacyMonolith()
    microservice = ModernMicroservice()
    facade = StranglerFacade(monolith, microservice)

    print("=== Iniciando Teste do Strangler Fig Pattern ===")

    # Teste 1: Requisição para usuário não migrado (deve ir para o monolito)
    res_legacy = facade.get_profile(99)
    print(f"Usuário 99 (Legado): {res_legacy}")
    assert res_legacy["source"] == "monolith", "Esperado processamento pelo monolito"

    # Teste 2: Requisição para usuário migrado (deve ir para o microsserviço)
    res_modern = facade.get_profile(1)
    print(f"Usuário 1 (Migrado): {res_modern}")
    assert res_modern["source"] == "microservice", "Esperado processamento pelo microsserviço"

    # Teste 3: Simulação de falha no microsserviço com acionamento de Fallback (Zero Downtime)
    # Forçamos uma exceção no microsserviço para validar o mecanismo de resiliência
    class FaultyMicroservice(ModernMicroservice):
        def get_user_profile(self, user_id: int) -> dict:
            raise ConnectionError("Microsserviço indisponível temporariamente")

    facade_with_fault = StranglerFacade(monolith, FaultyMicroservice())
    res_fallback = facade_with_fault.get_profile(1) # Usuário migrado, mas microsserviço cai
    print(f"Usuário 1 com falha no novo serviço (Fallback ativado): {res_fallback}")
    assert res_fallback["source"] == "monolith", "Deveria ter acionado o fallback para o monolito"

    print("=== Experimento executado com sucesso e todas as asserções passaram! ===")

if __name__ == "__main__":
    run_experiment()