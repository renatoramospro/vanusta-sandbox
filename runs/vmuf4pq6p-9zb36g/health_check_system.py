import asyncio
import time
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# --- 1. Implementação das Checagens Assíncronas com Timeout ---

async def check_database(should_fail: bool = False, latency: float = 0.02) -> dict:
    start = time.perf_counter()
    try:
        await asyncio.sleep(latency)
        if should_fail:
            raise ConnectionError("Falha na conexão com o PostgreSQL")
        return {
            "status": "healthy",
            "latency_ms": round((time.perf_counter() - start) * 1000, 2),
            "details": "Conexão estabelecida com sucesso"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "latency_ms": round((time.perf_counter() - start) * 1000, 2),
            "error": str(e)
        }

async def check_messaging(should_block: bool = False, latency: float = 0.02) -> dict:
    start = time.perf_counter()
    try:
        # Simula lentidão extrema se should_block for True (maior que o timeout individual)
        sleep_time = 0.5 if should_block else latency
        await asyncio.sleep(sleep_time)
        return {
            "status": "healthy",
            "latency_ms": round((time.perf_counter() - start) * 1000, 2),
            "details": "Broker RabbitMQ respondendo"
        }
    except asyncio.CancelledError:
        return {
            "status": "unhealthy",
            "latency_ms": round((time.perf_counter() - start) * 1000, 2),
            "error": "Timeout excedido na checagem de mensageria"
        }

async def run_health_checks(db_fail=False, msg_block=False, timeout=0.1) -> dict:
    """
    Executa os health checks em paralelo com timeout individual estrito
    e isolamento de falhas.
    """
    start_total = time.perf_counter()

    # Envolve cada checagem em um asyncio.wait_for para impor o timeout individual
    db_task = asyncio.wait_for(check_database(should_fail=db_fail), timeout=timeout)
    msg_task = asyncio.wait_for(check_messaging(should_block=msg_block), timeout=timeout)

    # Executa em paralelo e captura exceções/timeouts sem derrubar o processo
    results = await asyncio.gather(db_task, msg_task, return_exceptions=True)

    # Processamento do resultado do Banco de Dados
    if isinstance(results[0], asyncio.TimeoutError):
        db_result = {"status": "unhealthy", "latency_ms": timeout * 1000, "error": "Timeout estourado"}
    elif isinstance(results[0], Exception):
        db_result = {"status": "unhealthy", "latency_ms": 0.0, "error": str(results[0])}
    else:
        db_result = results[0]

    # Processamento do resultado da Mensageria
    if isinstance(results[1], asyncio.TimeoutError):
        msg_result = {"status": "unhealthy", "latency_ms": timeout * 1000, "error": "Timeout estourado"}
    elif isinstance(results[1], Exception):
        msg_result = {"status": "unhealthy", "latency_ms": 0.0, "error": str(results[1])}
    else:
        msg_result = results[1]

    # Regra de negócio para status global
    # Banco é crítico; mensageria é degradante
    global_status = "healthy"
    if db_result["status"] == "unhealthy":
        global_status = "unhealthy"
    elif msg_result["status"] == "unhealthy":
        global_status = "degraded"

    total_latency = round((time.perf_counter() - start_total) * 1000, 2)

    return {
        "status": global_status,
        "total_latency_ms": total_latency,
        dependencies: {
            "database": db_result,
            "messaging": msg_result
        }
    }


# --- 2. Testes Automatizados para Validar o Comportamento ---

async def run_tests():
    print("Iniciando testes do sistema de Health Check Assíncrono...")

    # Teste 1: Cenário saudável (todas as dependências respondem rápido)
    res_healthy = await run_health_checks(db_fail=False, msg_block=False)
    print(f"[Teste 1 - Saudável] Resultado: {json.dumps(res_healthy, indent=2)}")
    assert res_healthy["status"] == "healthy"
    assert res_healthy["total_latency_ms"] < 200, f"Latência acima do SLA: {res_healthy['total_latency_ms']}ms"

    # Teste 2: Isolamento de falha no Banco de Dados
    res_db_fail = await run_health_checks(db_fail=True, msg_block=False)
    print(f"[Teste 2 - Falha DB] Resultado: {json.dumps(res_db_fail, indent=2)}")
    assert res_db_fail["status"] == "unhealthy"
    assert res_db_fail["dependencies"]["database"]["status"] == "unhealthy"
    # Garante que a mensageria continuou saudável apesar da queda do banco (isolamento de falhas)
    assert res_db_fail["dependencies"]["messaging"]["status"] == "healthy"

    # Teste 3: Timeout individual estrito na Mensageria (trava simulada)
    res_timeout = await run_health_checks(db_fail=False, msg_block=True, timeout=0.05)
    print(f"[Teste 3 - Timeout Mensageria] Resultado: {json.dumps(res_timeout, indent=2)}")
    assert res_timeout["status"] == "degraded"
    assert res_timeout["dependencies"]["messaging"]["error"] == "Timeout estourado"
    # O timeout individual protegeu a latência total de estourar o SLA
    assert res_timeout["total_latency_ms"] < 200, f"Timeout não conteu a latência: {res_timeout['total_latency_ms']}ms"

    print("\nTodos os testes assíncronos passaram com sucesso!")

if __name__ == "__main__":
    asyncio.run(run_tests())