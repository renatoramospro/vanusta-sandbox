import threading
import time
import random
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class Report:
    stage: str
    content: str

@dataclass
class Mission:
    id: str
    current_stage: str
    version: int
    reports: List[Report]

class ConcurrencyError(Exception):
    """Exceção lançada quando uma atualização de versão falha."""
    pass

class MissionRepository:
    def __init__(self):
        self._storage: Dict[str, Mission] = {}
        self._lock = threading.Lock()  # Lock interno para simular atomicidade do DB

    def save(self, mission: Mission):
        with self._lock:
            existing = self._storage.get(mission.id)
            if existing:
                # Simulação de Optimistic Locking: 
                # O update só acontece se a versão no banco for igual à versão que a thread leu
                if existing.version != mission.version:
                    raise ConcurrencyError(f"Conflict detected for mission {mission.id}. Expected version {existing.version}, got {mission.version}")
                
                # Incrementa versão no sucesso
                mission.version += 1
                self._storage[mission.id] = mission
            else:
                mission.version = 1
                self._storage[mission.id] = mission

    def get(self, mission_id: str) -> Optional[Mission]:
        with self._lock:
            m = self._storage.get(mission_id)
            if m:
                # Retorna uma cópia para simular o objeto vindo do banco
                return Mission(m.id, m.current_stage, m.version, list(m.reports))
            return None

class WorkflowEngine:
    def __init__(self, repo: MissionRepository):
        self.repo = repo

    def advance(self, mission_id: str):
        # 1. READ
        mission = self.repo.get(mission_id)
        if not mission or mission.current_stage == 'architect':
            return

        # 2. PROCESS (Simula latência de processamento/I/O)
        # É aqui que a corrida acontece: as threads leem o mesmo estado antes de uma salvar
        time.sleep(random.uniform(0.01, 0.05))
        new_report = Report(stage='architect', content="Decomposição do problema realizada.")
        mission.reports.append(new_report)
        mission.current_stage = 'architect'

        # 3. WRITE (com verificação de versão)
        self.repo.save(mission)

def run_race_condition_test():
    repo = MissionRepository()
    engine = WorkflowEngine(repo)
    
    mission_id = "mission_123"
    # Inicializa missão
    repo.save(Mission(id=mission_id, current_stage='start', version=0, reports=[]))
    
    results = []
    errors = []

    def worker():
        try:
            engine.advance(mission_id)
            results.append("SUCCESS")
        except ConcurrencyError as e:
            errors.append(str(e))
            results.append("CONFLICT")
        except Exception as e:
            errors.append(f"UNEXPECTED: {str(e)}")
            results.append("ERROR")

    # Criar 5 threads tentando avançar a MESMA missão ao mesmo tempo
    threads = []
    for _ in range(5):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # VERIFICAÇÃO FINAL
    final_mission = repo.get(mission_id)
    
    print("--- RESULTADOS DO TESTE DE CONCORRÊNCIA ---")
    print(f"Chamadas bem sucedidas: {results.count('SUCCESS')}")
    print(f"Conflitos detectados (esperado): {results.count('CONFLICT')}")
    print(f"Relatórios de 'architect' encontrados: {len([r for r in final_mission.reports if r.stage == 'architect'])}")
    print(f"Versão final da missão: {final_mission.version}")
    
    # Critério de Sucesso: Exatamente 1 relatório
    assert len([r for r in final_mission.reports if r.stage == 'architect']) == 1, "ERRO: Duplicação de relatório detectada!"
    # Critério de Sucesso: Pelo menos uma chamada deve ter falhado por conflito (provando o lock)
    assert results.count('CONFLICT') > 0, "ERRO: Nenhuma colisão foi detectada. O sistema não está protegendo contra concorrência!"
    
    print("\nVEREDITO: SUCESSO. A trava de concorrência funcionou.")

if __name__ == "__main__":
    run_race_condition_test()