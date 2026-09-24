import asyncio
import contextvars
import json
import logging
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Optional
import pytest

# =====================================================================
# 1. GERENCIAMENTO DE CONTEXTO ASSÍNCRONO
# =====================================================================
correlation_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("correlation_id", default="")

def sanitize_correlation_id(corr_id: str) -> str:
    """Sanitiza o Correlation ID contra log injection (remove quebras de linha e limita tamanho)."""
    if not corr_id or not isinstance(corr_id, str):
        return "unknown"
    cleaned = "".join(c for c in corr_id if c.isalnum() or c in "-_")
    return cleaned[:128] if cleaned else "unknown"

# =====================================================================
# 2. FORMATADOR DE LOG ESTRUTURADO (JSON SEGURO)
# =====================================================================
class StructuredJsonFormatter(logging.Formatter):
    """
    Formata logs em JSON puro e estrito, injetando automaticamente o Correlation ID 
    e protegendo contra sobrescrita de campos de infraestrutura.
    """
    RESERVED_FIELDS = {"timestamp", "level", "message", "correlation_id", "logger"}

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "correlation_id": sanitize_correlation_id(correlation_id_ctx.get("N/A")),
            "logger": record.name
        }

        # Injeta propriedades customizadas com proteção estrita de campos reservados
        props = getattr(record, "props", None)
        if isinstance(props, dict):
            for key, value in props.items():
                if key in self.RESERVED_FIELDS:
                    raise ValueError(f"Tentativa de sobrescrever campo reservado de infraestrutura: '{key}'")
                log_entry[key] = value

        # Garante JSON estrito sem NaN/Infinity (allow_nan=False)
        try:
            return json.dumps(log_entry, allow_nan=False)
        except ValueError as e:
            raise ValueError(f"Falha na serialização JSON estrita (possível NaN/Inf): {e}")

# =====================================================================
# 3. COMPONENTES DA APLICAÇÃO (GATEWAY, SERVIÇO, BANCO E DOWNSTREAM)
# =====================================================================
logger = logging.getLogger("AppLogger")
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(StructuredJsonFormatter())
logger.handlers = [handler]
logger.setLevel(logging.INFO)
logger.propagate = False

async def gateway_middleware(correlation_id: str, request_payload: str):
    sanitized_id = sanitize_correlation_id(correlation_id)
    token = correlation_id_ctx.set(sanitized_id)
    try:
        logger.info("Gateway recebeu requisicao", extra={"props": {"path": "/api/v1/resource"}})
        result = await business_service(request_payload)
        return result
    finally:
        correlation_id_ctx.reset(token)

async def business_service(payload: str):
    logger.info("Servico processando payload", extra={"props": {"payload_size": len(payload)}})
    db_result = await database_layer_query("SELECT * FROM items")
    downstream_resp = HttpClientSimulation.get("http://external-api.local/v1/sync")
    return {"status": "success", "db": db_result, "downstream": downstream_resp}

async def database_layer_query(query: str):
    # Enriquecimento do log de query com o Correlation ID atual (sem persistir em tabela de domínio)
    logger.info("Executando query no banco de dados", extra={"props": {"sql": query, "db_system": "postgresql"}})
    await asyncio.sleep(0.01)
    return [{"id": 1, "name": "item-mock"}]

class HttpClientSimulation:
    @staticmethod
    def get(url: str) -> Dict[str, Any]:
        current_cid = correlation_id_ctx.get("N/A")
        # Simula a propagação downstream injetando o Correlation ID nos headers HTTP
        headers = {"X-Correlation-ID": current_cid}
        logger.info(f"Chamada HTTP downstream para {url}", extra={"props": {"http_headers": headers}})
        return {"url": url, "sent_correlation_id": current_cid, "status_code": 200}

# Propagação para Threads (run_in_executor)
def blocking_io_task(data: str) -> str:
    current_cid = correlation_id_ctx.get("N/A")
    return f"Processed {data} under CID: {current_cid}"

async def run_in_threadpool(executor, func, *args):
    ctx = contextvars.copy_context()
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, ctx.run, func, *args)

# =====================================================================
# 4. SUÍTE DE TESTES AUTOMATIZADOS (PYTEST + UNITTEST)
# =====================================================================
class TestStructuredLoggingAndCorrelation(unittest.TestCase):

    def test_json_formatter_valid_output(self):
        """Testa se o formatador produz JSON válido contendo o correlation_id."""
        token = correlation_id_ctx.set("test-cid-123")
        try:
            formatter = StructuredJsonFormatter()
            record = logging.LogRecord(
                name="TestLogger", level=logging.INFO, pathname="", lineno=0,
                msg="Mensagem de teste", exc_info=None, args=None
            )
            record.props = {"custom_field": "valid-value"}
            result = formatter.format(record)
            parsed = json.loads(result)

            self.assertEqual(parsed["correlation_id"], "test-cid-123")
            self.assertEqual(parsed["message"], "Mensagem de teste")
            self.assertEqual(parsed["custom_field"], "valid-value")
        finally:
            correlation_id_ctx.reset(token)

    def test_reserved_field_protection(self):
        """Garante que propriedades customizadas não podem sobrescrever campos reservados."""
        formatter = StructuredJsonFormatter()
        # Correção do erro de sintaxe anterior (parêntese fechado corretamente)
        record = logging.LogRecord(
            name="TestLogger", level=logging.INFO, pathname="", lineno=0,
            msg="Security test", exc_info=None, args=None
        )
        record.props = {"correlation_id": "malicious-override"}

        with self.assertRaises(ValueError):
            formatter.format(record)

    def test_json_strict_nan_rejection(self):
        """Testa se valores NaN geram erro e não produzem JSON inválido."""
        formatter = StructuredJsonFormatter()
        record = logging.LogRecord(
            name="TestLogger", level=logging.INFO, pathname="", lineno=0,
            msg="NaN test", exc_info=None, args=None
        )
        record.props = {"invalid_number": float("nan")}
        
        with self.assertRaises(ValueError):
            formatter.format(record)

    @pytest.mark.asyncio
    async def test_async_and_thread_propagation(self):
        """Testa a propagação de contextvars em asyncio e run_in_executor."""
        token = correlation_id_ctx.set("thread-test-cid-999")
        try:
            with ThreadPoolExecutor(max_workers=1) as pool:
                result = await run_in_threadpool(pool, blocking_io_task, "payload-abc")
                self.assertIn("thread-test-cid-999", result)
        finally:
            correlation_id_ctx.reset(token)

    def test_downstream_http_propagation(self):
        """Testa se o cliente HTTP injeta corretamente o Correlation ID nos cabeçalhos downstream."""
        token = correlation_id_ctx.set("downstream-cid-456")
        try:
            response = HttpClientSimulation.get("http://api.internal/service")
            self.assertEqual(response["sent_correlation_id"], "downstream-cid-456")
        finally:
            correlation_id_ctx.reset(token)

if __name__ == "__main__":
    unittest.main()