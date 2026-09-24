import asyncio
import time
import json

async def check_database(fail: bool = False, latency: float = 0.02) -> dict:
    """Simula a verificação de saúde do Banco de Dados com latência e possibilidade de falha."""
    start = time.perf_counter()
    try:
        await asyncio.sleep(latency)
        if fail:
            raise ConnectionError("Falha na conexão com o Banco de Dados")
        return {
            "status": "healthy",
            "latency_ms": round((time.perf_counter() - start) * 1000, 2)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "latency_ms": round((time.perf_counter() - start) * 1000, 2),
            "error": str(e)
        }

async def check_messaging(block: bool = False, latency: float = 0.03) -> dict:
    """Simula a verificação de saúde do sistema de Mensageria (RabbitMQ/Kafka)."""
    start = time.perf_counter()
    try:
        # Se block for True, simula travamento longo
        delay = 0.5 if block else latency
        await asyncio.sleep(delay)
        return {
            "status": "healthy",
            "latency_ms": round((time.perf_counter() - start) * 1000, 2)
        }
    except asyncio.TimeoutError:
        return {
            "status": "unhealthy",
            "latency_ms": round((time.perf_counter() - start) * 1000, 2),
            "error": "Timeout estourado"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "latency_ms": round((time.perf_counter() - start) * 1000, 2),
            "error": str(e)
        }

async def run_health_checks(db_fail: bool = False, msg_block: bool = False, timeout: float = 0.15) -> dict:
    """Executa as verificações em paralelo com timeouts individuais e isolamento de falhas."""
    start_total = time.perf_counter()

    # Aplicação de timeout individual estrito para cada dependência
    db_task = asyncio.wait_for(check_database(fail=db_fail), timeout=timeout)
    msg_task = asyncio.wait_for(check_messaging(block=msg_block), timeout=timeout)

    # Executa concorrentemente e captura exceções/timeouts sem derrubar o conjunto
    results = await asyncio.gather(db_task, msg_task, return_exceptions=True)

    total_latency = round((time.perf_counter() - start_total) * 1000, 2)

    # Processamento do resultado do Banco
    db_res = results[0]
    if isinstance(db_res, Exception) or isinstance(db_res, asyncio.TimeoutError):
        db_status = {"status": "unhealthy", "latency_ms": timeout * 1000, "error": "Timeout estourado ou falha crítica"}
    else:
        db_status = db_res

    # Processamento do resultado da Mensageria
    msg_res = results[1]
    if isinstance(msg_res, Exception) or isinstance(msg_res, asyncio.TimeoutError):
        msg_status = {"status": "unhealthy", "latency_ms": timeout * 1000, "error": "Timeout estourado"}
    else:
        msg_status = msg_res

    # Determinação do status global (Banco é crítico, Mensageria é degradável)
    overall_status = "healthy"
    if db_status["status"] == "unhealthy":
        overall_status = "unhealthy"
    elif msg_status["status"] == "unhealthy":
        overall_status = "degraded"

    # Construção rigorosa do payload detalhado
    report = {
        "status": overall_status,
        "total_latency_ms": total_latency,
        "dependencies": {
            "database": db_status,
            "messaging": msg_status
        }
    }
    return report

async def run_tests():
    print("Iniciando testes do sistema de Health Check Assíncrono...")

    # Teste 1: Sistema totalmente saudável
    res_healthy = await run_health_checks(db_fail=False, msg_block=False)
    print(f"[Teste 1 - Saudável] Resultado: {json.dumps(res_healthy, indent=2)}")
    assert res_healthy["status"] == "healthy"
    assert res_healthy["total_latency_ms"] < 200

    # Teste 2: Falha isolada no Banco de Dados
    res_db_fail = await run_health_checks(db_fail=True, msg_block=False)
    print(f"[Teste 2 - Falha BD] Resultado: {json.dumps(res_db_fail, indent=2)}")
    assert res_db_fail["status"] == "unhealthy"
    assert res_db_fail["dependencies"]["database"]["status"] == "unhealthy"
    assert res_db_fail["dependencies"]["messaging"]["status"] == "healthy"

    # Teste 3: Timeout individual estrito na Mensageria (travamento simulado)
    res_timeout = await run_health_checks(db_fail=False, msg_block=True, timeout=0.05)
    print(f"[Teste 3 - Timeout Mensageria] Resultado: {json.dumps(res_timeout, indent=2)}")
    assert res_timeout["status"] == "degraded"
    assert res_timeout["dependencies"]["messaging"]["error"] == "Timeout estourado"
    assert res_timeout["total_latency_ms"] < 200, f"Latência excedeu o SLA: {res_timeout['total_latency_ms']}ms"

    print("\nTodos os testes assíncronos passaram com sucesso!")

if __name__ == "__main__":
    asyncio.run(run_tests())