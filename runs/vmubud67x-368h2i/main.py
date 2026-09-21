import time
from typing import Dict, List, Any

class NormalizadorCI:
    """Ataca o equívoco de que diferentes ferramentas de CI/CD possuem payloads padronizados.
    Realiza a normalização para um esquema canônico único."""
    
    @staticmethod
    def normalizar_github(payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "projeto": payload.get("repository", {}).get("name", "desconhecido"),
            "tempo_build_segundos": payload.get("workflow_run", {}).get("duration_ms", 0) / 1000.0,
            "cobertura_testes": payload.get("metrics", {}).get("test_coverage", 0.0),
            "lead_time_horas": payload.get("workflow_run", {}).get("lead_time_sec", 0) / 3600.0
        }

    @staticmethod
    def normalizar_gitlab(payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "projeto": payload.get("project", {}).get("name", "desconhecido"),
            "tempo_build_segundos": payload.get("build", {}).get("duration", 0),
            "cobertura_testes": payload.get("object_attributes", {}).get("coverage", 0.0),
            "lead_time_horas": payload.get("pipeline", {}).get("lead_time", 0.0)
        }


class FrameworkMonitoramento:
    """Framework principal de monitoramento em tempo real para projetos de software."""
    
    def __init__(self, limiares: Dict[str, float]):
        self.eventos: List[Dict[str, Any]] = []
        self.limiares = limiares # Ex: {'max_build_sec': 300, 'min_cobertura': 80.0}

    def ingerir_evento(self, origem: str, payload: Dict[str, Any]):
        if origem == "github":
            evento_normalizado = NormalizadorCI.normalizar_github(payload)
        elif origem == "gitlab":
            evento_normalizado = NormalizadorCI.normalizar_gitlab(payload)
        else:
            raise ValueError(f"Origem desconhecida: {origem}")
        
        self.eventos.append(evento_normalizado)

    def gerar_relatorio_consolidado(self) -> Dict[str, Any]:
        if not self.eventos:
            return {"total_eventos_processados": 0}

        total = len(self.eventos)
        soma_build = sum(e["tempo_build_segundos"] for e in self.eventos)
        soma_cobertura = sum(e["cobertura_testes"] for e in self.eventos)
        soma_lead_time = sum(e["lead_time_horas"] for e in self.eventos)

        media_build = soma_build / total
        media_cobertura = soma_cobertura / total
        media_lead_time = soma_lead_time / total

        # Verificação de Limiares / Alertas Automatizados
        alertas = []
        for evento in self.eventos:
            if evento["tempo_build_segundos"] > self.limiares.get("max_build_sec", 300):
                alertas.append(f"ALERTA: Projeto '{evento['projeto']}' excedeu o tempo de build ({evento['tempo_build_segundos']}s > {self.limiares['max_build_sec']}s)")
            if evento["cobertura_testes"] < self.limiares.get("min_cobertura", 80.0):
                alertas.append(f"ALERTA: Projeto '{evento['projeto']}' abaixo da cobertura mínima ({evento['cobertura_testes']}% < {self.limiares['min_cobertura']}%)")

        return {
            "media_tempo_build": media_build,
            "media_cobertura_testes": media_cobertura,
            "media_velocidade_entrega": media_lead_time,
            "total_eventos_processados": total,
            "alertas_ativos": alertas
        }


if __name__ == "__main__":
    # Configurando limiares críticos
    limiares_projeto = {
        "max_build_sec": 300.0, # 5 minutos
        "min_cobertura": 80.0    # 80%
    }
    
    framework = FrameworkMonitoramento(limiares_projeto)
    
    # 1. Simulando payload do GitHub Actions (Pipeline 1)
    payload_gh = {
        "repository": {"name": "projeto-alfa-github"},
        "workflow_run": {"duration_ms": 180000, "lead_time_sec": 15120}, # 180s (OK), 4.2h
        "metrics": {"test_coverage": 85.5} # 85.5% (OK)
    }
    
    # 2. Simulando payload do GitLab CI (Pipeline 2)
    payload_gl = {
        "project": {"name": "projeto-beta-gitlab"},
        "build": {"duration": 350, "status": "success"}, # 350s (Estoura limiar de 300s)
        "object_attributes": {"coverage": 75.0},         # 75% (Estoura limiar de 80%)
        "pipeline": {"lead_time": 6.5}                   # 6.5h
    }
    
    print("Ingerindo evento do Pipeline 1 (GitHub Actions)...")
    framework.ingerir_evento("github", payload_gh)
    
    print("Ingerindo evento do Pipeline 2 (GitLab CI)...")
    framework.ingerir_evento("gitlab", payload_gl)
    
    print("\nGerando relatório consolidado...")
    inicio_teste = time.time()
    relatorio = framework.gerar_relatorio_consolidado()
    fim_teste = time.time()
    
    print(f"\n--- RELATÓRIO DE DESEMPENHO EM TEMPO REAL ---")
    print(f"Tempo médio de build: {relatorio['media_tempo_build']:.2f} segundos")
    print(f"Média de cobertura de testes: {relatorio['media_cobertura_testes']:.2f}%")
    print(f"Média de velocidade de entrega (Lead Time): {relatorio['media_velocidade_entrega']:.2f} horas")
    print(f"Total de eventos processados: {relatorio['total_eventos_processados']}")
    print(f"\nAlertas disparados pelo sistema:")
    for alerta in relatorio['alertas_ativos']:
        print(f" - {alerta}")
        
    duracao_relatorio = fim_teste - inicio_teste
    print(f"\n[Sucesso] Relatório gerado em {duracao_relatorio:.6f} segundos (Abaixo do limite estipulado de 5s).")
    
    # Assert explícito para garantir sucesso na execução do teste automatizado
    assert duracao_relatorio < 5.0, "O relatório excedeu o tempo limite de 5 segundos!"
    assert relatorio['total_eventos_processados'] == 2, "Deveria ter processado exatamente 2 eventos."
    assert len(relatorio['alertas_ativos']) == 2, "Deveria ter disparado exatamente 2 alertas de violação."