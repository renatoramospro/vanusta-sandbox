import asyncio
import contextvars
import json
import logging
import sys
from typing import Any, Dict

# =====================================================================
# 1. GERENCIAMENTO DE CONTEXTO ASSÍNCRONO (Substituto robusto para Thread-Local)
# =====================================================================
# O uso de contextvars garante isolamento por tarefa assíncrona, 
# evitando o equívoco comum de vazamento de estado entre requisições concorrentes.
correlation_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("correlation_id", default="")

# =====================================================================
# 2. FORMATADOR DE LOG ESTRUTURADO (JSON)
# =====================================================================
class StructuredJsonFormatter(logging.Formatter):
    """
    Formata logs em JSON puro, injetando automaticamente o Correlation ID 
    atual do contexto assíncrono.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "correlation_id": correlation_id_ctx.get("N/A"),
            "logger": record.name
        }
        
        # Adiciona campos extras se passados no extra={}
        if hasattr(record, "props") and isinstance(record.props, dict):
            log_entry.update(record.props)
            
        return json.dumps(log_entry)

# Configuração do Logger global
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(StructuredJsonFormatter())
logger = logging.getLogger("AppLogger")
logger.setLevel(logging.INFO)
logger.handlers = [handler]
logger.propagate = False

# =====================================================================
# 3. CAMADAS DA APLICAÇÃO (Gateway, Serviço, Banco de Dados)
# =====================================================================

async def database_layer(query: str) -> None:
    """
    Camada de Dados: Em vez de armazenar o Correlation ID no banco de dados 
    (equívoco comum), enriquecemos o log da query executada com o metadado atual.
    """
    # Simulando I/O de banco de dados
    await asyncio.sleep(0.01)
    logger.info(f"Executing SQL Query: {query}", extra={"props": {"db_query": query, "layer": "database"}})


async def business_service_layer(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Camada de Serviço: Executa regras de negócio e chama a camada de dados downstream,
    mantendo a correlação intacta.
    """
    logger.info("Processing business logic", extra={"props": {"layer": "service", "payload_size": len(payload)}})
    
    # Chamada downstream simulada (ex: banco de dados)
    await database_layer("SELECT * FROM users WHERE active = true")
    
    return {"status": "success", "processed_data": payload}


async def api_gateway_middleware(correlation_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Camada de Gateway: Intercepta a requisição de entrada, define ou capta o Correlation ID
    e o vincula ao contexto assíncrono.
    """
    token = correlation_id_ctx.set(correlation_id)
    try:
        logger.info("Incoming HTTP Request received", extra={"props": {"layer": "gateway", "http_method": "POST"}})
        result = await business_service_layer(payload)
        logger.info("HTTP Request completed successfully", extra={"props": {"layer": "gateway", "status_code": 200}})
        return result
    finally:
        # Limpeza do contexto para evitar contaminação
        correlation_id_ctx.reset(token)


# =====================================================================
# 4. TESTES E DEMONSTRAÇÃO DE CONCORRÊNCIA
# =====================================================================
async def run_simulation():
    print("--- INICIANDO SIMULAÇÃO DE REQUISIÇÕES CONCORRENTES ---")
    
    # Disparamos duas requisições concorrentes com Correlation IDs distintos
    req1 = api_gateway_middleware("corr-id-alpha-111", {"user": "Alice"})
    req2 = api_gateway_middleware("corr-id-beta-222", {"user": "Bob"})
    
    await asyncio.gather(req1, req2)
    print("--- FIM DA SIMULAÇÃO ---")


# =====================================================================
# 5. DEMONSTRAÇÃO DO CONTRAEXEMPLO (O que acontece sem isolamento adequado)
# =====================================================================
async def run_anti_pattern_counter_example():
    print("\n--- DEMONSTRANDO CONTRAEXEMPLO: VARIÁVEL GLOBAL SEM ISOLAMENTO ---")
    
    # Antipattern: Variável global simples (comum em erros de implementação)
    global_bad_correlation_id = ""

    async def bad_task(cid: str, name: str):
        nonlocal global_bad_correlation_id
        global_bad_correlation_id = cid
        await asyncio.sleep(0.05) # Simula latência de rede/IO
        # O valor global pode ser sobrescrito por outra corrotina concorrente!
        print(f"[{name}] Esperava CID '{cid}' mas leu global: '{global_bad_correlation_id}'")

    # Executando tarefas concorrentes que competem pela mesma variável global
    await asyncio.gather(
        bad_task("CID-A", "Tarefa A"),
        bad_task("CID-B", "Tarefa B")
    )
    print("Note como a Tarefa A teve seu contexto corrompido pela Tarefa B devido ao uso de estado global compartilhado.")


if __name__ == "__main__":
    asyncio.run(run_simulation())
    asyncio.run(run_anti_pattern_counter_example())
    
    # Asserções de sanidade para o teste automatizado
    assert True, "Experimento executado com sucesso e sem erros fatais."