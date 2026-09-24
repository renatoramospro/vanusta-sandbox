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
            "correlation_id": correlation_id_ctx.get("N/A"),
            "logger": record.name
        }
        
        # Adiciona campos extras com proteção contra sobrescrita de campos reservados
        if hasattr(record, "props") and isinstance(record.props, dict):
            for key, value in record.props.items():
                if key in self.RESERVED_FIELDS:
                    # Renomeia ou ignora para evitar colisão maliciosa/acidental
                    log_entry[f"user_{key}"] = value
                else:
                    log_entry[key] = value
            
        # allow_nan=False garante conformidade estrita com JSON (rejeita NaN, Infinity)
        return json.dumps(log_entry, allow_nan=False)

# Configuração do Logger
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(StructuredJsonFormatter())
logger = logging.getLogger("SecureAppLogger")
logger.setLevel(logging.INFO)
logger.handlers = [handler]
logger.propagate = False

# =====================================================================
# 3. PROPAGAÇÃO PARA THREADS (run_in_executor)
# =====================================================================
async def run_in_threadpool(executor, func, *args):
    """
    Propaga explicitamente o contextvar para threads usando contextvars.copy_context().
    """
    ctx = contextvars.copy_context()
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, ctx.run, func, *args)

def blocking_io_task(data: str) -> str:
    # Acessa o contextvar corretamente dentro da thread propagada
    cid = correlation_id_ctx.get()
    logger.info("Executing blocking I/O operation", extra={"props": {"data": data, "layer": "database"}})
    return f"Processed {data} with CID {cid}"

# =====================================================================
# 4. PROPAGAÇÃO DOWNSTREAM HTTP
# =====================================================================
class HttpClientSimulation:
    """
    Simula um cliente HTTP downstream que injeta automaticamente o Correlation ID nos headers.
    """
    @staticmethod
    def get(url: str) -> Dict[str, Any]:
        cid = correlation_id_ctx.get()
        headers = {"X-Correlation-ID": cid}
        logger.info(f"Outgoing HTTP GET to {url}", extra={"props": {"downstream_url": url, "headers": headers}})
        return {"status": 200, "sent_correlation_id": cid}

# =====================================================================
# 5. TESTES UNITÁRIOS E DE INTEGRAÇÃO (PYTEST)
# =====================================================================
class TestStructuredLoggingAndCorrelation(unittest.TestCase):

    def test_json_formatter_prevents_override(self):
        """Testa se props de usuário não conseguem sobrescrever campos reservados de infraestrutura."""
        formatter = StructuredJsonFormatter()
        record = logging.LogRecord(
            name="Test", level=logging.INFO, pathname="", lineno=0,
            msg="Test message", exc_info=None, args=None
        )
        # Tenta injetar correlation_id e timestamp maliciosos via props
        record.props = {
            "correlation_id": "malicious-override-id",
            "timestamp": "fake-time",
            "custom_field": "valid-value"
        }
        
        correlation_id_ctx.set("real-correlation-123")
        output = formatter.format(record)
        parsed = json.loads(output)

        self.assertEqual(parsed["correlation_id"], "real-correlation-123")
        self.assertEqual(parsed["user_correlation_id"], "malicious-override-id")
        self.assertEqual(parsed["user_timestamp"], "fake-time")
        self.assertEqual(parsed["custom_field"], "valid-value")

    def test_json_strict_nan_rejection(self):
        """Testa se valores NaN geram erro e não produzem JSON inválido."""
        formatter = StructuredJsonFormatter()
        record = logging.LogRecord(
            name="Test", level=logging.INFO, pathname="", lineno=0,
            msg="NaN test", exc_info=None, args=None
        }
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