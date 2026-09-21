import time
import json
import hashlib
from typing import Dict, List, Any, Optional

class GitRepository:
    """Simula um repositório Git corporativo (Fonte da Verdade)."""
    def __init__(self):
        self.commits: List[Dict[str, Any]] = []
        # Commit inicial (Estado Estável Válido)
        self.commit("feat: configuração inicial estável", {"replicas": 3, "timeout": 30, "status_code": 200})

    def commit(self, message: str, config: Dict[str, Any]) -> str:
        parent = self.commits[-1]["hash"] if self.commits else None
        config_str = json.dumps(config, sort_keys=True)
        commit_hash = hashlib.sha256(f"{message}{config_str}{time.time()}".encode()).hexdigest()[:8]
        
        commit_data = {
            "hash": commit_hash,
            "parent": parent,
            "message": message,
            "config": config
        }
        self.commits.append(commit_data)
        return commit_hash

    def get_latest_commit(self) -> Dict[str, Any]:
        return self.commits[-1]

    def get_commit_by_hash(self, commit_hash: str) -> Optional[Dict[str, Any]]:
        for c in self.commits:
            if c["hash"] == commit_hash:
                return c
        return None


class AuditLogger:
    """Garante registro de auditoria imutável correlacionando commits e eventos."""
    def __init__(self):
        self.logs: List[Dict[str, Any]] = []

    def log(self, event_type: str, commit_hash: str, details: str):
        entry = {
            "timestamp": time.time(),
            "event": event_type,
            "commit_hash": commit_hash,
            "details": details
        }
        self.logs.append(entry)
        print(f"[AUDIT] {event_type} | Commit: {commit_hash} | Detalhes: {details}")

    def get_history(self) -> List[Dict[str, Any]]:
        return self.logs


class ClusterState:
    """Simula o ambiente de execução (Cluster Kubernetes/Container)."""
    def __init__(self):
        self.current_config: Dict[str, Any] = {}
        self.active_commit: Optional[str] = None
        self.health_status: bool = True

    def apply(self, commit: Dict[str, Any]) -> bool:
        print(f"[CLUSTER] Aplicando configuração do commit {commit['hash']} ({commit['message']})...")
        self.current_config = commit["config"]
        self.active_commit = commit["hash"]
        # Simula validação interna de health check com base na configuração aplicada
        if self.current_config.get("status_code", 200) != 200:
            self.health_status = False
            return False
        self.health_status = True
        return True


class GitOpsAgent:
    """Agente de Sincronização Contínua e Rollback Automático."""
    def __init__(self, repo: GitRepository, cluster: ClusterState, auditor: AuditLogger):
        self.repo = repo
        self.cluster = cluster
        self.auditor = auditor
        self.last_synced_commit: Optional[str] = None

    def reconcile(self) -> bool:
        latest = self.repo.get_latest_commit()
        
        if latest["hash"] == self.last_synced_commit:
            return True # Já está sincronizado

        print(f"\n[GITOPS] Desvio detectado. Sincronizando para o commit: {latest['hash']}")
        start_time = time.time()

        # Tenta aplicar o estado desejado
        success = self.cluster.apply(latest)
        
        sync_duration = time.time() - start_time

        if not success:
            print(f"[GITOPS] ALERTA: Falha no Health Check pós-deploy detectada em {sync_duration:.2f}s!")
            self.auditor.log("DEPLOY_FAILED", latest["hash"], "Health check falhou após aplicação.")
            
            # Dispara Rollback Automático
            self.trigger_rollback(latest["hash"])
            return False

        if sync_duration > 120:
            print(f"[GITOPS] ALERTA: Timeout de sincronização (> 120s). Disparando rollback.")
            self.trigger_rollback(latest["hash"])
            return False

        self.last_synced_commit = latest["hash"]
        self.auditor.log("DEPLOY_SUCCESS", latest["hash"], faplicado com sucesso em {sync_duration:.2f}s")
        return True

    def trigger_rollback(self, failed_commit_hash: str):
        print(f"[GITOPS] Iniciando protocolo de Rollback para o commit defeituoso {failed_commit_hash}...")
        
        # Localiza o commit anterior seguro (Parent do commit falho)
        failed_commit = self.repo.get_commit_by_hash(failed_commit_hash)
        if not failed_commit or not failed_commit["parent"]:
            print("[GITOPS] ERRO CRÍTICO: Nenhum estado anterior disponível para rollback!")
            self.auditor.log("ROLLBACK_CRITICAL_FAILURE", failed_commit_hash, "Sem commit pai.")
            return

        previous_commit = self.repo.get_commit_by_hash(failed_commit["parent"])
        if not previous_commit:
            print("[GITOPS] ERRO CRÍTICO: Commit pai não encontrado no repositório.")
            return

        print(f"[GITOPS] Revertendo para estado estável seguro: {previous_commit['hash']} ({previous_commit['message']})")
        
        rollback_start = time.time()
        success = self.cluster.apply(previous_commit)
        rollback_duration = time.time() - rollback_start

        if success and rollback_duration <= 120:
            self.last_synced_commit = previous_commit["hash"]
            self.auditor.log("ROLLBACK_SUCCESS", failed_commit_hash, f"Revertido para {previous_commit['hash']} em {rollback_duration:.2f}s")
            print(f"[GITOPS] Rollback concluído com sucesso dentro da janela temporal de 2 minutos.")
        else:
            self.auditor.log("ROLLBACK_FAILED", failed_commit_hash, "Falha ao reaplicar estado anterior ou timeout.")
            print(f"[GITOPS] Falha crítica no rollback.")


# --- Teste de Execução e Demonstração Concreta ---
if __name__ == "__main__":
    repo = GitRepository()
    auditor = AuditLogger()
    cluster = ClusterState()
    agent = GitOpsAgent(repo, cluster, auditor)

    print("--- FASE 1: Sincronização Inicial (Estado Válido) ---")
    agent.reconcile()
    assert cluster.active_commit == repo.get_latest_commit()["hash"]
    print("✓ Estado inicial sincronizado com sucesso.\n")

    print("--- FASE 2: Introdução de Configuração Inválida (Simulação de Falha & Rollback) ---")
    # Commit com erro proposital (status_code 500 simulando falha de health check)
    bad_commit_hash = repo.commit("fix: atualizar configuração com erro crítico", {"replicas": 5, "timeout": 10, "status_code": 500})
    
    # Executa reconciliação que deve detectar a falha e realizar rollback automático
    agent.reconcile()

    # Verificações de segurança e critério de sucesso
    print("\n--- FASE 3: Verificação de Auditoria e Estado Final ---")
    history = auditor.get_history()
    print(f"Total de eventos auditados: {len(history)}")
    
    # Confirma que o cluster voltou para o commit estável anterior após o rollback
    initial_hash = repo.commits[0]["hash"]
    assert cluster.active_commit == initial_hash, f"Esperado cluster no commit {initial_hash}, mas está em {cluster.active_commit}"
    print(f"✓ Validação de Rollback bem-sucedida: Cluster retornou ao estado estável {initial_hash}.")
    print("✓ Todos os testes do experimento GitOps concluídos com sucesso.")