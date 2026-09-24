import hmac
import hashlib
import time
import json
import unittest

class WebhookManager:
    def __init__(self, secret: str, tolerance_seconds: int = 300):
        self.secret = secret.encode('utf-8')
        self.tolerance_seconds = tolerance_seconds

    def generate_signature(self, payload_bytes: bytes, timestamp: int) -> str:
        """
        Gera a assinatura HMAC-SHA256 combinando o timestamp e o raw body.
        Formato assinado: "timestamp.raw_body"
        """
        signed_payload = f"{timestamp}.".encode('utf-8') + payload_bytes
        signature = hmac.new(
            self.secret,
            msg=signed_payload,
            digestmod=hashlib.sha256
        ).hexdigest()
        return signature

    def verify_webhook(self, payload_bytes: bytes, signature_header: str, timestamp_header: int) -> bool:
        """
        Valida o webhook verificando:
        1. Se a requisição está dentro da janela temporal permitida.
        2. Se a assinatura HMAC é válida usando tempo constante.
        """
        current_time = int(time.time())
        
        # 1. Proteção contra Replay Attack (Janela de 5 minutos / 300 segundos)
        if abs(current_time - timestamp_header) > self.tolerance_seconds:
            return False

        # 2. Recálculo da assinatura esperada
        expected_signature = self.generate_signature(payload_bytes, timestamp_header)

        # 3. Proteção contra Timing Attacks (Comparação em tempo constante)
        # hmac.compare_digest previne ataques de canal lateral baseados no tempo de execução da string comparison
        return hmac.compare_digest(expected_signature, signature_header)


class TestWebhookSecurity(unittest.TestCase):
    def setUp(self):
        self.secret = "sua_chave_secreta_super_segura"
        self.manager = WebhookManager(secret=self.secret)
        self.payload_dict = {"event": "payment.approved", "amount": 150.00}
        self.raw_body = json.dumps(self.payload_dict, separators=(',', ':')).encode('utf-8')
        self.now = int(time.time())

    def test_valid_webhook(self):
        """Testa o fluxo de sucesso com assinatura válida e timestamp atual."""
        sig = self.manager.generate_signature(self.raw_body, self.now)
        is_valid = self.manager.verify_webhook(self.raw_body, sig, self.now)
        self.assertTrue(is_valid, "O webhook válido deveria ser aceito.")
        print("[SUCESSO] Webhook válido aceito corretamente.")

    def test_invalid_signature_tampered_body(self):
        """Testa a rejeição quando o corpo da mensagem é adulterado."""
        sig = self.manager.generate_signature(self.raw_body, self.now)
        
        # Atacante altera o corpo da requisição
        tampered_body = json.dumps({"event": "payment.approved", "amount": 9999.00}, separators=(',', ':')).encode('utf-8')
        
        is_valid = self.manager.verify_webhook(tampered_body, sig, self.now)
        self.assertFalse(is_valid, "O webhook com payload adulterado DEVE ser rejeitado.")
        print("[SUCESSO] Webhook adulterado rejeitado com sucesso.")

    def test_expired_timestamp(self):
        """Testa a rejeição de requisições antigas (fora da janela de 5 minutos)."""
        old_timestamp = self.now - 301  # 301 segundos atrás (> 5 minutos)
        sig = self.manager.generate_signature(self.raw_body, old_timestamp)
        
        is_valid = self.manager.verify_webhook(self.raw_body, sig, old_timestamp)
        self.assertFalse(is_valid, "O webhook com timestamp expirado DEVE ser rejeitado.")
        print("[SUCESSO] Webhook com timestamp expirado rejeitado com sucesso.")

    def test_timing_attack_protection_simulation(self):
        """Demonstra conceitualmente que a comparação usa tempo constante."""
        sig = self.manager.generate_signature(self.raw_body, self.now)
        fake_sig = "a" * len(sig)
        
        # Validando que uma assinatura totalmente incorreta retorna False de forma segura
        is_valid = self.manager.verify_webhook(self.raw_body, fake_sig, self.now)
        self.assertFalse(is_valid)
        print("[SUCESSO] Assinatura incorreta rejeitada via compare_digest (Tempo Constante).")


if __name__ == '__main__':
    # Executa a suíte de testes unitários exigida pelos critérios de sucesso
    suite = unittest.TestLoader().loadTestsFromTestCase(TestWebhookSecurity)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if not result.wasSuccessful():
        exit(1)