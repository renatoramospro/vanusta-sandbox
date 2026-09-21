path=framework_monitoramento.py
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
            "velocidade_entrega_horas": payload.get("metrics", {}).get("lead_time_hours", 0.0),
            "status": payload.get("workflow_run", {}).get("conclusion", "success")
        }

    @staticmethod
    def normalizar_gitlab(payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "projeto": payload.get("project", {}).get("name", "desconhecido"),
            "tempo_build_segundos": payload.get("build", {}).get("duration", 0),
            "cobertura_testes": payload.get("object_attributes", {}).get("coverage", 0.0),
            "velocidade_entrega_horas": payload.get("pipeline", {}).get("lead_time", 0.0),
            "status": payload.get("build", {}).get("status", "success")
        }


class FrameworkMonitoramento:
    """Framework principal de coleta, análise e relatórios em tempo real."""
    
    def __init__(self, thresholds: Dict[str, float]):
        self.eventos_normalizados: List[Dict[str, Any]] = []
        self.thresholds = thresholds # Limiares para alertas (ex: cobertura mínima, tempo máximo)
        self.alertas_disparados: List[str] = []

    def ingerir_evento(self, origem: str, payload: Dict[str, Any]) -> None:
        if origem == "github":
            evento = NormalizadorCI.normalizar_github(payload)
        elif origem == "gitlab":
            evento = NormalizadorCI.normalizar_gitlab(payload)
        else:
            raise ValueError(f"Origem desconhecida: {origem}")
            
        self.eventos_normalizados.append(evento)
        self.avaliar_alertas(evento)

    def avaliar_alertas(self, evento: Dict[str, Any]) -> None:
        """Verifica se o evento viola as regras de desempenho estabelecidas."""
        projeto = evento["projeto"]
        
        if evento["cobertura_testes"] < self.thresholds.get("cobertura_minima", 80.0):
            self.alertas_disparados.append(
                f"[ALERTA] Projeto '{projeto}': Cobertura de testes ({evento['cobertura_testes']}%) abaixo do limiar!"
            )
            
        if evento["tempo_build_segundos"] > self.thresholds.get("tempo_build_maximo", 600.0):
            self.alertas_disparados.append(
                f"[ALERTA] Projeto '{projeto}': Tempo de build ({evento['tempo_build_segundos']}s) acima do limiar!"
            )

    def gerar_relatorio_consolidado(self) -> Dict[str, Any]:
        """Gera o relatório consolidado em tempo real, garantindo latência < 5 segundos."""
        inicio = time.time()
        
        total_projetos = len(self.eventos_normalizados)
        if total_projetos == 0:
            return {"status": "sem_dados"}
            
        soma_build = sum(e["tempo_build_segundos"] for e in self.eventos_normalizados)
        soma_cobertura = sum(e["cobertura_testes"] for e in self.eventos_normalizados)
        soma_lead_time = sum(e["velocidade_entrega_horas"] for e in self.eventos_normalizados)
        
        relatorio = {
            "media_tempo_build": soma_build / total_projetos,
            "media_cobertura_testes": soma_cobertura / total_projetos,
            "media_velocidade_entrega": soma_lead_time / total_projetos,
            "total_eventos_processados": total_projetos,
            "alertas_ativos": self.alertas_disparados
        }
        
        tempo_decorrido = time.time() - inicio
        assert tempo_decorrido < 5.0, "O relatório excedeu o limite de 5 segundos!"
        
        return relatorio


# ==========================================
# TESTES E DEMONSTRAÇÃO PRÁTICA DO EXPERIMENTO
# ==========================================
if __name__ == "__main__":
    print("Iniciando o Framework de Monitoramento de Métricas em Tempo Real...")
    
    # Configurando limiares de alerta (ex: cobertura mínima de 80%, build máximo de 300s)
    limiares = {
        "cobertura_minima": 80.0,
        "tempo_build_maximo": 300.0
    }
    
    framework = FrameworkMonitoramento(limiares)
    
    # 1. Simulando payload do GitHub Actions (Pipeline 1)
    payload_gh = {
        "repository": {"name": "projeto-alpha-github"},
        "workflow_run": {"duration_ms": 150000, "conclusion": "success"}, # 150 segundos
        "metrics": {"test_coverage": 85.5, "lead_time_hours": 4.2}
    }
    
    # 2. Simulando payload do GitLab CI (Pipeline 2)
    payload_gl = {
        "project": {"name": "projeto-beta-gitlab"},
        "build": {"duration": 350, "status": "success"}, # 350 segundos (Vai estourar o limiar de 300s!)
        "object_attributes": {"coverage": 75.0}, # 75% (Vai estourar o limiar de 80%!)
        "pipeline": {"lead_time": 6.5}
    }
    
    # Ingestão em tempo real
    print("Ingerindo evento do Pipeline 1 (GitHub Actions)...")
    framework.ingerir_evento("github", payload_gh)
    
    print("Ingerindo evento do Pipeline 2 (GitLab CI)...")
    framework.ingerir_evento("gitlab", payload_gl)
    
    # Geração do Relatório Consolidado
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
        
    print(f"\n[Sucesso] Relatório gerado em {(fim_teste - inicio_teste):.4f} segundos (Abaixo do limite de 5s).")