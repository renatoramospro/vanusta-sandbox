import time
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class DatabaseState:
    node_id: str
    is_healthy: bool = True
    last_replicated_tx: int = 1000
    replication_lag_seconds: float = 0.0

@dataclass
class DataCenter:
    dc_id: str
    region: str
    is_active: bool = False
    db: DatabaseState = field(default_factory=lambda: DatabaseState("db-init"))
    consecutive_failures: int = 0

class GlobalTrafficManager:
    def __init__(self, dcs: List[DataCenter], failure_threshold: int = 2):
        self.dcs = dcs
        self.active_dc: Optional[DataCenter] = None
        self.failure_threshold = failure_threshold
        self._bootstrap_initial_dc()

    def _bootstrap_initial_dc(self):
        for dc in self.dcs:
            if dc.db.is_healthy:
                dc.is_active = True
                self.active_dc = dc
                print(f"[GTM] Inicializado com {dc.dc_id} ({dc.region}) como Primário.")
                break

    def perform_deep_health_check(self, dc: DataCenter) -> bool:
        """
        Health check profundo: valida conectividade, sanidade do banco e lag de replicação.
        Equívoco evitado: Evita health checks superficiais (HTTP 200) que não testam o banco.
        """
        if not dc.db.is_healthy:
            return False
        # Simula verificação de lag de replicação aceitável (RPO)
        if dc.db.replication_lag_seconds > 5.0:
            return False
        return True

    def evaluate_and_failover(self) -> str:
        """
        Avalia o estado dos data centers, aplicando threshold para evitar flapping
        e aciona o failover seguro se o primário cair.
        """
        if not self.active_dc:
            return "NO_ACTIVE_DC"

        # Verifica saúde do DC ativo atual
        is_healthy = self.perform_deep_health_check(self.active_dc)
        
        if is_healthy:
            # Reseta contador de falhas se estiver saudável
            self.active_dc.consecutive_failures = 0
            return "NO_CHANGE"
        
        # Incrementa falhas consecutivas para evitar flapping por instabilidade transitória
        self.active_dc.consecutive_failures += 1
        print(f"[GTM] ALERTA: Falha detectada no DC ativo {self.active_dc.dc_id}. Contagem: {self.active_dc.consecutive_failures}/{self.failure_threshold}")

        if self.active_dc.consecutive_failures >= self.failure_threshold:
            print(f"[GTM] Threshold de falhas atingido para {self.active_dc.dc_id}. Iniciando Failover...")
            return self._execute_failover()

        return "NO_CHANGE"

    def _execute_failover(self) -> str:
        old_active = self.active_dc
        best_candidate: Optional[DataCenter] = None
        
        # Encontra o melhor candidato secundário baseado na menor defasagem de transação (RPO)
        valid_candidates = [dc for dc in self.dcs if dc.dc_id != old_active.dc_id and self.perform_deep_health_check(dc)]
        
        if not valid_candidates:
            print("[GTM] ERRO CRÍTICO: Nenhum Data Center secundário saudável disponível para promoção!")
            return "FAILOVER_FAILED"

        # Seleciona o candidato com o maior número de transações replicadas (menor perda de dados)
        best_candidate = max(valid_candidates, key=lambda x: x.db.last_replicated_tx)

        # Executa a transição de tráfego
        old_active.is_active = False
        best_candidate.is_active = True
        self.active_dc = best_candidate
        
        print(f"[GTM] SUCESSO: Tráfego redirecionado de {old_active.dc_id} para {best_candidate.dc_id}.")
        print(f"[GTM] Novo DC Primário: {best_candidate.dc_id} | Transação base: {best_candidate.db.last_replicated_tx}")
        return "FAILOVER_SUCCESS"

def run_simulation():
    print("=== INICIANDO SIMULAÇÃO DE FAILOVER MULTI-DATA CENTER ===")
    
    dc1 = DataCenter(dc_id="DC-US-EAST", region="us-east-1", db=DatabaseState("db-us-east", True, 5000, 0.1))
    dc2 = DataCenter(dc_id="DC-EU-WEST", region="eu-west-1", db=DatabaseState("db-eu-west", True, 4995, 0.5))
    
    gtm = GlobalTrafficManager(dcs=[dc1, dc2], failure_threshold=2)
    
    # 1. Operação normal
    status = gtm.evaluate_and_failover()
    assert status == "NO_CHANGE"
    assert gtm.active_dc.dc_id == "DC-US-EAST"
    
    # 2. Injeção de Falha no DC Primário
    print("\n[Injeção] Simulando queda catastrófica no DC-US-EAST...")
    dc1.db.is_healthy = False
    
    # Ciclo 1 de detecção (falha 1/2)
    status1 = gtm.evaluate_and_failover()
    assert status1 == "NO_CHANGE"
    
    # Ciclo 2 de detecção (atinge threshold e dispara failover)
    status2 = gtm.evaluate_and_failover()
    assert status2 == "FAILOVER_SUCCESS"
    assert gtm.active_dc.dc_id == "DC-EU-WEST"
    assert gtm.active_dc.is_active is True
    assert dc1.is_active is False
    
    print("\n=== TODOS OS TESTES DE FAILOVER EXECUTADOS COM SUCESSO ===")

if __name__ == "__main__":
    run_simulation()