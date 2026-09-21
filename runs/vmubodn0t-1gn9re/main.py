py
path=failover_simulator.py
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
        # Seleciona o primeiro DC saudável como primário inicial
        for dc in self.dcs:
            if dc.db.is_healthy:
                dc.is_active = True
                self.active_dc = dc
                print(f"[GTM] Inicializado com {dc.dc_id} ({dc.region}) como Primário.")
                break

    def perform_deep_health_check(self, dc: DataCenter) -> bool:
        """
        Health check profundo: valida conectividade, sanidade do banco e lag de replicação.
        Equívoco evitado: Não checa apenas 'ping' ou 'HTTP 200' superficial.
        """
        if not dc.db.is_healthy:
            return False
        
        # Simula verificação de lag de replicação (RPO check)
        if dc.db.replication_lag_seconds > 5.0:
            print(f"[HealthCheck] ALERTA: {dc.dc_id} com lag de replicação excessivo ({dc.db.replication_lag_seconds}s).")
            return False
            
        return True

    def evaluate_and_failover(self) -> str:
        """
        Monitora os DCs, detecta falhas em < 5s simulados e executa o failover se necessário.
        """
        print(f"\n[GTM] Executando ciclo de monitoramento de saúde...")
        
        # Verifica o DC ativo atual
        if self.active_dc:
            is_healthy = self.perform_deep_health_check(self.active_dc)
            if not is_healthy:
                self.active_dc.consecutive_failures += 1
                print(f"[GTM] FALHA DETECTADA em {self.active_dc.dc_id}! Contagem de falhas: {self.active_dc.consecutive_failures}/{self.failure_threshold}")
                
                if self.active_dc.consecutive_failures >= self.failure_threshold:
                    return self._execute_failover()
            else:
                # Reseta contador se estiver saudável
                self.active_dc.consecutive_failures = 0
                print(f"[GTM] DC Ativo {self.active_dc.dc_id} operando normalmente.")
        
        return "NO_CHANGE"

    def _execute_failover(self) -> str:
        old_dc = self.active_dc
        old_dc.is_active = False
        
        print(f"[Failover] Iniciando transição de tráfego saindo de {old_dc.dc_id}...")
        
        # Encontra o melhor candidato secundário baseado em saúde e RPO mínimo
        candidates = [dc for dc in self.dcs if dc.dc_id != old_dc.dc_id and self.perform_deep_health_check(dc)]
        
        if not candidates:
            print("[Failover CRÍTICO] Nenhum Data Center secundário saudável disponível! Risco de Downtime total.")
            return "FAILOVER_FAILED"
            
        # Seleciona candidato com menor lag de replicação (garantindo RPO controlado)
        best_candidate = min(candidates, key=lambda x: x.db.replication_lag_seconds)
        
        # Promove o novo DC
        best_candidate.is_active = True
        self.active_dc = best_candidate
        
        print(f"[Failover SUCESSO] Tráfego redirecionado para {best_candidate.dc_id} ({best_candidate.region}). RTO atendido.")
        return "FAILOVER_SUCCESS"

# --- SIMULAÇÃO E TESTES DE CARGA ---
def run_simulation():
    print("=== INICIANDO SIMULAÇÃO DE FAILOVER MULTI-DC (VANUSTA-CORE) ===")
    
    dc1 = DataCenter(dc_id="DC-US-EAST", region="us-east-1", db=DatabaseState("db-us-east", True, 5000, 0.1))
    dc2 = DataCenter(dc_id="DC-EU-WEST", region="eu-west-1", db=DatabaseState("db-eu-west", True, 4995, 0.5))
    
    gtm = GlobalTrafficManager(dcs=[dc1, dc2])
    
    # 1. Operação normal
    status = gtm.evaluate_and_failover()
    assert status == "NO_CHANGE"
    assert gtm.active_dc.dc_id == "DC-US-EAST"
    
    # 2. Injeção de Falha no DC Primário (simulando queda de rede/energia)
    print("\n[Injeção] Simulando queda catastrófica no DC-US-EAST...")
    dc1.db.is_healthy = False
    
    # Ciclo 1 de detecção (falha 1/2)
    status1 = gtm.evaluate_and_failover()
    assert status1 == "NO_CHANGE" # Ainda aguarda threshold para evitar falso positivo por instabilidade transitória
    
    # Ciclo 2 de detecção (atinge threshold e dispara failover)
    status2 = gtm.evaluate_and_failover()
    assert status2 == "FAILOVER_SUCCESS"
    assert gtm.active_dc.dc_id == "DC-EU-WEST"
    assert gtm.active_dc.is_active is True
    assert dc1.is_active is False
    
    print("\n=== TODOS OS TESTES DE FAILOVER EXECUTADOS COM SUCESSO ===")

if __name__ == "__main__":
    run_simulation()