import hmac
import hashlib
import time
import unittest

class WebhookManager:
    def __init__(self, secret: str, tolerance_seconds: int = 300):
        self.secret = secret.encode('utf-8')
        self.tolerance_seconds = tolerance_seconds
        # Armazenamento em memória para deduplicação (Prevenção contra Replay Attack)
        self.processed_events = set()

    def generate_signature(self, payload_bytes: bytes, timestamp: int, event_id: str) -> str:
        """
        Gera a assinatura HMAC-SHA256 combinando timestamp, event_id e o raw body.
        Formato assinado: "timestamp.event_id.raw_body"
        """
        signed_payload = f"{timestamp}.{event_id}.".encode('utf-8') + payload_bytes
        signature = hmac.new(
            self.secret,
            msg=signed_payload,
            digestmod=hashlib.sha256
        ).hexdigest()
        return signature

    def verify_webhook(
        self, 
        payload_bytes: bytes, 
        signature_header: str, 
        timestamp_header, 
        event_id_header
    ) -> bool:
        """
        Valida o webhook verificando:
        1. Cabeçalhos obrigatórios presentes e não None/vazios.
        2. Tipos de dados corretos (timestamp inteiro, event_id e signature string).
        3. Janela temporal (respeitando tolerância de 5 minutos / 300 segundos).
        4. Deduplicação (anti-replay via event_id).
        5. Assinatura HMAC válida usando hmac.compare_digest (tempo constante).
        """
        # 1. Guarda contra cabeçalhos ausentes ou nulos
        if not signature_header or timestamp_header is None or not event_id_header:
            return False

        # 2. Guarda contra tipos inválidos
        if not isinstance(timestamp_header, (int, float)) or not isinstance(event_id_header, str) or not isinstance(signature_header, str):
            return False

        # 3. Validação da Janela Temporal (Fresco / Replay Temporal)
        current_time = int(time.time())
        try:
            ts_int = int(timestamp_header)
        except (ValueError, TypeError):
            return False

        if abs(current_time - ts_int) > self.tolerance_seconds:
            return False

        # 4. Deduplicação (Prevenção contra Replay de Evento Válido)
        if event_id_header in self.processed_events:
            return False

        # 5. Cálculo e verificação da assinatura HMAC usando tempo constante
        expected_signature = self.generate_signature(payload_bytes, ts_int, event_id_header)
        
        # hmac.compare_digest previne timing attacks comparando em tempo constante
        if not hmac.compare_digest(expected_signature.encode('utf-8'), signature_header.encode('utf-8')):
            return False

        # Regista o evento como processado após validação bem-sucedida
        self.processed_events.add(event_id_header)
        return True


class TestWebhookSecurity(unittest.TestCase):
    def setUp(self):
        # String genérica para evitar falsos positivos de detecção de segredo em ambiente público
        self.secret = "exemplo_de_chave_secreta_compartilhada_para_testes"
        self.manager = WebhookManager(self.secret, tolerance_seconds=300)
        self.raw_body = b'{"evento":"transacao.criada","valor":150.00}'
        self.now = int(time.time())

    def test_valid_webhook(self):
        """Testa o fluxo de sucesso com payload íntegro e cabeçalhos corretos."""
        event_id = "evt_sucesso_001"
        sig = self.manager.generate_signature(self.raw_body, self.now, event_id)
        
        is_valid = self.manager.verify_webhook(self.raw_body, sig, self.now, event_id)
        self.assertTrue(is_valid, "O webhook válido deve ser aceito.")
        print("[SUCESSO] Webhook válido aceito corretamente.")

    def test_replay_attack_prevention(self):
        """Testa se o mesmo evento enviado duas vezes é rejeitado (Deduplicação)."""
        event_id = "evt_replay_002"
        sig = self.manager.generate_signature(self.raw_body, self.now, event_id)
        
        # Primeira chamada: deve passar
        self.assertTrue(self.manager.verify_webhook(self.raw_body, sig, self.now, event_id))
        
        # Segunda chamada (Replay): deve ser rejeitada
        is_valid_replay = self.manager.verify_webhook(self.raw_body, sig, self.now, event_id)
        self.assertFalse(is_valid_replay, "O webhook duplicado (replay) deve ser rejeitado.")
        print("[SUCESSO] Replay attack prevenido com sucesso via event_id.")

    def test_missing_or_none_headers(self):
        """Testa o comportamento defensivo com cabeçalhos nulos ou ausentes."""
        event_id = "evt_headers_003"
        sig = self.manager.generate_signature(self.raw_body, self.now, event_id)
        
        self.assertFalse(self.manager.verify_webhook(self.raw_body, None, self.now, event_id))
        self.assertFalse(self.manager.verify_webhook(self.raw_body, sig, None, event_id))
        self.assertFalse(self.manager.verify_webhook(self.raw_body, sig, self.now, None))
        print("[SUCESSO] Cabeçalhos ausentes ou None rejeitados de forma controlada.")

    def test_invalid_types(self):
        """Testa a rejeição de tipos de dados inválidos nos cabeçalhos."""
        event_id = "evt_types_004"
        sig = self.manager.generate_signature(self.raw_body, self.now, event_id)
        
        # Timestamp como string não numérica ou tipo inválido
        self.assertFalse(self.manager.verify_webhook(self.raw_body, sig, "nao_e_um_inteiro", event_id))
        # Event ID como inteiro em vez de string
        self.assertFalse(self.manager.verify_webhook(self.raw_body, sig, self.now, 12345))
        print("[SUCESSO] Tipos inválidos rejeitados com segurança.")

    def test_tampered_payload(self):
        """Testa a rejeição quando o corpo da requisição é adulterado."""
        event_id = "evt_tamper_005"
        sig = self.manager.generate_signature(self.raw_body, self.now, event_id)
        
        tampered_body = b'{"evento":"transacao.criada","valor":999.99}'
        is_valid = self.manager.verify_webhook(tampered_body, sig, self.now, event_id)
        self.assertFalse(is_valid, "O webhook com payload adulterado deve ser rejeitado.")
        print("[SUCESSO] Payload adulterado rejeitado com sucesso.")

    def test_expired_timestamp(self):
        """Testa a rejeição de requisições fora da janela de tolerância de 5 minutos."""
        event_id = "evt_expired_006"
        old_timestamp = self.now - 305  # 305 segundos atrás (> 300s)
        sig = self.manager.generate_signature(self.raw_body, old_timestamp, event_id)
        
        is_valid = self.manager.verify_webhook(self.raw_body, sig, old_timestamp, event_id)
        self.assertFalse(is_valid, "O webhook com timestamp expirado deve ser rejeitado.")
        print("[SUCESSO] Webhook com timestamp expirado rejeitado com sucesso.")

    def test_timing_attack_protection(self):
        """Demonstra e valida o uso seguro de hmac.compare_digest contra timing attacks."""
        event_id = "evt_timing_007"
        sig = self.manager.generate_signature(self.raw_body, self.now, event_id)
        
        # Assinatura falsa com o mesmo comprimento para testar a comparação constante
        fake_sig = "a" * len(sig)
        
        is_valid = self.manager.verify_webhook(self.raw_body, fake_sig, self.now, event_id)
        self.assertFalse(is_valid)
        print("[SUCESSO] Assinatura incorreta rejeitada via compare_digest em tempo constante.")


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestWebhookSecurity)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if not result.wasSuccessful():
        exit(1)