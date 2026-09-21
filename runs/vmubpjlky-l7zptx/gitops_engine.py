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


class AuditLog:
    """Trilha de auditoria imutável para eventos de GitOps."""
    def __init__(self):
        self.logs: List[Dict[str, Any]] = []

    def log(self, event_type: str, commit_hash: str, details: str):
        entry = {
            "timestamp": time.time(),
            "event_type": event_type,
            "commit_hash": commit_hash,
            "details": details
        }
        self.logs.append(entry)
        print(f"[AUDIT] {event_type} | Commit: {commit_hash} | {details}")

    def get_history(self) -> List[Dict[str, Any]]:
        return self.logs


class Cluster:
    """Simula o ambiente de execução (Cluster Kubernetes / Infraestrutura)."""
    def __init__(self):
        self.active_config: Dict[str, Any] = {}
        self.active_commit: Optional[str] = None

    def apply(self, commit_hash: str, config: Dict[str, Any]) -> bool:
        self.active_config = config
        self.active_commit = commit_hash
        return True

    def health_check(self) -> bool:
        """Avalia a sanidade operacional do serviço pós-deploy."""
        return self.active_config.get("status_code", 200) == 200


class GitOpsAgent:
    """Agente de Reconciliação Contínua e Rollback Automático."""
    def __init__(self, repo: GitRepository, cluster: Cluster, auditor: AuditLog):
        self.repo = repo
        self.cluster = cluster
        self.auditor = auditor
        self.last_synced_commit: Optional[str] = None

    def reconcile(self) -> bool:
        """Executa o ciclo de sincronização entre Git e Cluster."""
        latest = self.repo.get_latest_commit()
        
        if self.last_synced_commit == latest["hash"]:
            return True # Já está sincronizado

        print(f"\n[AGENTE] Detectada nova versão no Git: {latest['hash']} ({latest['message']})")
        start_time = time.time()
        
        # Tenta aplicar a configuração
        self.cluster.apply(latest["hash"], latest["config"])
        
        # Subsistema de Validação e Health Check
        time.sleep(0.1) # Simula tempo de propagação/startup
        if self.cluster.health_check():
            sync_duration = time.time() - start_time
            self.last_synced_commit = latest["hash"]
            self.auditor.log("DEPLOY_SUCCESS", latest["hash"], f"Aplicado com sucesso em {sync_duration:.2f}s")
            return True
        else:
            print(f"[AGENTE] ALERTA: Health check falhou para o commit {latest['hash']}! Iniciando Rollback automático...")
            self.rollback(latest["hash"])
            return False

    def rollback(self, failed_commit_hash: str):
        """Executa rollback automático para o último estado estável conhecido."""
        rollback_start = time.time()
        
        # Encontra o commit pai/anterior válido
        failed_commit = self.repo.get_commit_by_hash(failed_commit_hash)
        parent_hash = failed_commit.get("parent") if failed_commit else None
        
        if parent_hash:
            stable_commit = self.repo.get_commit_by_hash(parent_hash)
        else:
            # Fallback para o primeiro commit se não houver pai explícito
            stable_commit = self.repo.commits[0]

        # Aplica o estado estável anterior no cluster
        self.cluster.apply(stable_commit["hash"], stable_commit["config"])
        self.last_synced_commit = stable_commit["hash"]
        
        rollback_duration = time.time() - rollback_start
        self.auditor.log("ROLLBACK_SUCCESS", stable_commit["hash"], f"Rollback de {failed_commit_hash} executado com sucesso em {rollback_duration:.2f}s (Estado restaurado para {stable_commit['hash']})")


if __name__ == "__main__":
    print("=== INICIANDO EXPERIMENTO DE GITOPS ===")
    repo = GitRepository()
    auditor = AuditLog()
    cluster = Cluster()
    agent = GitOpsAgent(repo, cluster, auditor)

    # Fase 1: Sincronização bem-sucedida (Commit inicial)
    print("\n--- FASE 1: Sincronização Inicial Válida ---")
    agent.reconcile()
    assert cluster.health_check() == True, "O cluster deveria estar saudável na fase 1"

    # Fase 2: Introdução de um commit defeituoso (Falha de Health Check e Rollback)
    print("\n--- FASE 2: Deploy de Configuração Defeituosa (Gatilho de Rollback) ---")
    bad_commit_hash = repo.commit("feat: alterar configuração com erro", {"replicas": 5, "timeout": 10, "status_code": 500})
    
    # Executa a reconciliação que deve detectar a falha e disparar o rollback
    success = agent.reconcile()
    assert success == False, "A reconciliação deveria falhar devido ao health check"

    # Fase 3: Verificação de Auditoria e Estado Final
    print("\n--- FASE 3: Verificação de Auditoria e Estado Final ---")
    history = auditor.get_history()
    print(f"Total de eventos auditados: {len(history)}")
    
    # Confirma que o cluster voltou para o commit estável anterior após o rollback
    initial_hash = repo.commits[0]["hash"]
    assert cluster.active_commit == initial_hash, f"Esperado cluster no commit {initial_hash}, mas está em {cluster.active_commit}"
    print(f"✓ Validação de Rollback bem-sucedida: Cluster retornou ao estado estável {initial_hash}.")
    print("✓ Todos os testes do experimento GitOps concluídos com sucesso.")