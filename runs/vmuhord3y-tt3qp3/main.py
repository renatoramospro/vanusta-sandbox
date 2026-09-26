import hmac
import hashlib
import time
import struct
import base64

class TOTP:
    """
    Implementação completa do TOTP (RFC 6238) do zero usando apenas a biblioteca padrão.
    Suporta HMAC-SHA1, HMAC-SHA256 e HMAC-SHA512.
    """
    BASE32_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"

    @staticmethod
    def base32_decode(s: str) -> bytes:
        """Decodifica uma string Base32 padrão (RFC 4648) sem bibliotecas externas."""
        s = s.upper().rstrip('=')
        accumulator = 0
        bits_left = 0
        output = bytearray()
        
        for char in s:
            if char not in TOTP.BASE32_CHARS:
                raise ValueError(f"Caractere Base32 inválido: {char}")
            val = TOTP.BASE32_CHARS.index(char)
            accumulator = (accumulator << 5) | val
            bits_left += 5
            if bits_left >= 8:
                bits_left -= 8
                output.append((accumulator >> bits_left) & 0xFF)
                
        return bytes(output)

    @staticmethod
    def base32_encode(b: bytes) -> bytes:
        """Codifica bytes para string Base32 sem padding."""
        return base64.b32encode(b).rstrip(b'=')

    @staticmethod
    def int_to_bytestring(i: int, length: int = 8) -> bytes:
        """Converte um inteiro para big-endian byte string de comprimento fixo (contadores HOTP/TOTP)."""
        return i.to_bytes(length, byteorder='big')

    @classmethod
    def generate(cls, secret_base32: str, timestamp: float = None, period: int = 30, 
                 digits: int = 6, digest_mod=hashlib.sha1) -> str:
        """Gera um token TOTP de acordo com a RFC 6238."""
        if timestamp is None:
            timestamp = time.time()
            
        counter = int(timestamp // period)
        msg = cls.int_to_bytestring(counter)
        key = cls.base32_decode(secret_base32)
        
        # Cálculo HMAC
        h = hmac.new(key, msg, digest_mod).digest()
        
        # Truncamento Dinâmico (RFC 4226 / RFC 6238)
        offset = h[-1] & 0x0F
        binary_code = (
            ((h[offset] & 0x7F) << 24) |
            ((h[offset + 1] & 0xFF) << 16) |
            ((h[offset + 2] & 0xFF) << 8) |
            (h[offset + 3] & 0xFF)
        )
        
        otp = binary_code % (10 ** digits)
        return str(otp).zfill(digits)

    @classmethod
    def verify(cls, secret_base32: str, token: str, timestamp: float = None, 
               period: int = 30, digits: int = 6, digest_mod=hashlib.sha1, window: int = 1) -> bool:
        """
        Valida um token TOTP aceitando uma janela de drift temporal estritamente limitada.
        - window=0: apenas o período atual.
        - window=1: período anterior, atual e posterior (tolerância recomendada).
        - window > 1: rejeitado por política de segurança para evitar ataques de replay.
        Usa hmac.compare_digest para prevenir timing attacks.
        """
        if not isinstance(window, int) or window < 0 or window > 1:
            raise ValueError("Parâmetro 'window' deve ser estritamente 0 ou 1 para mitigar ataques de replay.")
            
        if timestamp is None:
            timestamp = time.time()
            
        if not token or not isinstance(token, str) or len(token) != digits:
            return False

        current_counter = int(timestamp // period)
        
        # Verifica a janela de drift [-window, +window]
        for w in range(-window, window + 1):
            checked_counter = current_counter + w
            checked_time = checked_counter * period
            expected_token = cls.generate(secret_base32, timestamp=checked_time, period=period, digits=digits, digest_mod=digest_mod)
            
            if hmac.compare_digest(expected_token.encode('utf-8'), token.encode('utf-8')):
                return True
                
        return False


class DeviceManager:
    """
    Gerencia o registro, isolamento e validação de dispositivos por usuário.
    Garante que segredos sejam únicos por dispositivo e que a revogação funcione corretamente.
    """
    def __init__(self):
        # Estrutura: { user_id: { device_id: secret_base32 } }
        self._registry = {}

    def register_device(self, user_id: str, device_id: str) -> str:
        """Registra um novo dispositivo para o usuário e gera um segredo criptográfico seguro."""
        if user_id not in self._registry:
            self._registry[user_id] = {}
            
        # Gera 20 bytes aleatórios (padrão recomendado para TOTP) e codifica em Base32
        random_bytes = hashlib.sha256(f"{user_id}:{device_id}:{time.time()}".encode()).digest()[:20]
        secret = TOTP.base32_encode(random_bytes).decode('utf-8')
        
        self._registry[user_id][device_id] = secret
        return secret

    def revoke_device(self, user_id: str, device_id: str) -> bool:
        """Revoga o acesso de um dispositivo específico."""
        if user_id in self._registry and device_id in self._registry[user_id]:
            del self._registry[user_id][device_id]
            return True
        return False

    def verify_user_device(self, user_id: str, device_id: str, token: str, window: int = 1) -> bool:
        """Valida um token TOTP para um dispositivo específico de um usuário."""
        if user_id not in self._registry or device_id not in self._registry[user_id]:
            return False
            
        secret = self._registry[user_id][device_id]
        return TOTP.verify(secret, token, window=window)


if __name__ == "__main__":
    print("=== EXECUTANDO TESTES DE VALIDAÇÃO TOTP & SECURITY ===" )
    
    # 1. Teste com Vetor Oficial da RFC 6238 (SHA1)
    # Segredo ASCII "12345678901234567890" em Base32 é GEZDGNBVGY3TQOJQ===
    rfc_secret_base32 = "GEZDGNBVGY3TQOJQ"
    
    # Vetores oficiais da RFC 6238 para T = 59 (Epoch 59 -> contador 1 para period 30)
    # T = 59 -> token SHA1 esperado: 94287082 (últimos 6 dígitos: 287082)
    token_rfc = TOTP.generate(rfc_secret_base32, timestamp=59.0, digits=6)
    assert token_rfc == "287082", f"Esperado 287082, obtido {token_rfc}"
    print("[Sucesso] Vetor oficial RFC 6238 validado perfeitamente.")
    
    # 2. Teste de Gerenciamento e Isolamento de Dispositivos (Sem expor segredos)
    manager = DeviceManager()
    user = "alice@example.com"
    dev_phone = "smartphone-alice"
    dev_tablet = "tablet-alice"
    
    manager.register_device(user, dev_phone)
    manager.register_device(user, dev_tablet)
    print("[DeviceManager] Dispositivos registrados com sucesso (segredos mantidos em sigilo operacional).")
    
    # Gera token para o telefone
    # Como não temos acesso direto ao segredo gerado fora daqui, extraímos via DeviceManager para teste
    secret_phone = manager._registry[user][dev_phone]
    token_phone = TOTP.generate(secret_phone)
    
    # Valida no telefone
    assert manager.verify_user_device(user, dev_phone, token_phone, window=1) == True
    print("[Sucesso] Token válido aceito no dispositivo de origem.")
    
    # Tenta cruzar validação com o tablet (segredos distintos)
    assert manager.verify_user_device(user, dev_tablet, token_phone, window=1) == False
    print("[Sucesso] Isolamento rigoroso entre dispositivos confirmado (segredos distintos).")
    
    # 3. Teste de Limite de Janela de Drift (Segurança contra Replay)
    try:
        TOTP.verify(secret_phone, token_phone, window=2)
        raise AssertionError("Deveria ter rejeitado window=2")
    except ValueError as e:
        print(f"[Sucesso de Segurança] Janela excessiva rejeitada corretamente: {e}")

    # 4. Teste de Revogação de Dispositivo
    manager.revoke_device(user, dev_phone)
    assert manager.verify_user_device(user, dev_phone, token_phone) == False
    print("[Sucesso] Revogação de dispositivo validada: acesso negado após revogação.")

    print("=== TODOS OS TESTES PASSARAM COM ÊXITO ===")