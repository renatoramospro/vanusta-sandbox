import time
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

# ==========================================
# 1. SETUP DE CRIPTOGRAFIA (Chaves Assimétricas)
# ==========================================
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)
public_key = private_key.public_key()

private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)
public_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

# ==========================================
# 2. COMPONENTE: AUTH SERVER (Emissor)
# ==========================================
def issue_game_session_token(player_id: str, session_jti: str) -> str:
    """
    Emite um JWT assinado com a chave privada contendo claims restritas
    ao contexto de jogo (expiração curta e jti único para rastreio de replay).
    """
    now = time.time()
    payload = {
        "sub": player_id,
        "jti": session_jti,
        "iat": now,
        "nbf": now - 5,  # Tolerância de 5 segundos para clock drift na emissão
        "exp": now + 300, # Sessão válida por 5 minutos
        "iss": "game-auth-provider"
    }
    return jwt.encode(payload, private_pem, algorithm="RS256")

# ==========================================
# 3. COMPONENTE: GAME SERVER (Distributed Session & JTI Manager)
# ==========================================
class DistributedGameSessionManager:
    """
    Gerenciador de sessões preparado para arquitetura distribuída (múltiplos nós).
    Simula um backend atômico compartilhado (como Redis SETNX com TTL) para
    impedir replay attacks entre servidores de jogo diferentes atrás de um load balancer.
    """
    def __init__(self):
        # Simula armazenamento distribuído (ex: Redis cluster) em vez de dicionário local isolado
        self.distributed_jti_store = {}

    def _atomic_acquire_jti(self, jti: str, ttl: int) -> bool:
        """
        Simula a operação atômica de lock/registro de JTI (equivalente a SETNX no Redis).
        Retorna True se o JTI é inédito e foi registrado com sucesso.
        Retorna False se o JTI já foi utilizado (tentativa de replay).
        """
        current_time = time.time()
        
        # Limpeza de chaves expiradas na store simulada
        expired_keys = [k for k, exp_t in self.distributed_jti_store.items() if exp_t <= current_time]
        for k in expired_keys:
            del self.distributed_jti_store[k]

        if jti in self.distributed_jti_store:
            return False  # Replay detectado!

        # Registra o JTI com tempo de expiração correspondente ao TTL do token
        self.distributed_jti_store[jti] = current_time + ttl
        return True

    def authenticate_player_handshake(self, token: str) -> dict:
        """
        Valida o token JWT localmente (< 5ms) configurando explicitamente o 'leeway'
        para tolerância de clock drift e aplicando verificação atômica de JTI distribuído.
        """
        try:
            # Decodifica e valida o token usando a chave pública RSA
            # O parâmetro leeway=5 lida com pequenas discrepâncias de relógio (clock drift) entre nós.
            payload = jwt.decode(
                token,
                public_pem,
                algorithms=["RS256"],
                options={"verify_signature": True, "verify_exp": True, "verify_nbf": True},
                leeway=5
            )
        except jwt.ExpiredSignatureError:
            raise PermissionError("Token expirado.")
        except jwt.InvalidTokenError as e:
            raise PermissionError(f"Token inválido: {e}")

        # Extrai o identificador único de sessão (jti)
        jti = payload.get("jti")
        if not jti:
            raise PermissionError("Token sem identificador de sessão (jti) obrigatório.")

        # Calcula o TTL remanescente do token para expirar o registro do JTI no store distribuído
        token_ttl = int(payload["exp"] - time.time())
        if token_ttl <= 0:
            raise PermissionError("Token já expirado.")

        # Proteção contra Replay Attack de forma distribuída e atômica
        if not self._atomic_acquire_jti(jti, token_ttl):
            raise PermissionError("Ataque de repetição (Replay Attack) detectado: JTI já utilizado em um nó do cluster!")

        return payload

# ==========================================
# 4. EXECUÇÃO DE TESTES E DEMONSTRAÇÃO
# ==========================================
if __name__ == "__main__":
    print("=== INICIALIZANDO TESTES DE SEGURANÇA OAUTH2 + JWT (DISTRIBUÍDO) ===")
    
    server_manager = DistributedGameSessionManager()
    player_id = "player_alpha_99"
    session_jti = "session-unique-xyz-123"

    # Passo 1: Emissão do token válido pelo Auth Server
    token_valido = issue_game_session_token(player_id, session_jti)
    print(f"[AUTH SERVER] Token emitido com sucesso para {player_id} (JTI: {session_jti})")

    print("\n--- TESTE 1: Handshake Inicial Válido ---")
    session_data = server_manager.authenticate_player_handshake(token_valido)
    print(f"Sucesso! Jogador autenticado: {session_data['sub']}")
    print("Teste 1 APROVADO.\n")

    print("--- TESTE 2: Ataque de Repetição (Replay Attack) em Cluster Distribuído ---")
    try:
        # Tentativa de reutilizar o mesmo token/JTI (simulando outro nó ou reconexão maliciosa imediata)
        server_manager.authenticate_player_handshake(token_valido)
        raise AssertionError("Deveria ter falhado por replay attack!")
    except PermissionError as e:
        print(f"Defesa bem-sucedida contra Replay Distribuído: {e}")
        print("Teste 2 APROVADO: Replay attack bloqueado atomicamente em ambiente distribuído.\n")

    print("--- TESTE 3: Verificação de Clock Drift com Leeway ---")
    # Emitimos um token com nbf ligeiramente no futuro (simulando clock drift de 3 segundos)
    now = time.time()
    drift_payload = {
        "sub": "player_drift",
        "jti": "drift-jti-456",
        "iat": now,
        "nbf": now + 3,  # Válido apenas daqui a 3 segundos
        "exp": now + 300,
        "iss": "game-auth-provider"
    }
    drift_token = jwt.encode(drift_payload, private_pem, algorithm="RS256")
    
    # Com leeway=5 configurado no decodificador, a pequena diferença de relógio é aceita com sucesso
    drift_data = server_manager.authenticate_player_handshake(drift_token)
    print(f"Sucesso! Token com clock drift aceito graças ao parâmetro leeway: {drift_data['sub']}")
    print("Teste 3 APROVADO.\n")

    print("--- TESTE 4: Contraexemplo de Falha (Validação ingênua sem verificação atômica de jti) ---")
    def insecure_naive_validation(token):
        return jwt.decode(token, public_pem, algorithms=["RS256"])

    # Na validação ingênua, o token pode ser processado infinitamente em múltiplos servidores
    payload_reutilizado = insecure_naive_validation(token_valido)
    print(f"[AVISO DE SEGURANÇA] Na abordagem ingênua, o token do player {payload_reutilizado['sub']} "
          f"seria aceito em múltiplos nós do cluster porque a assinatura RSA permanece válida matematicamente.")
    print("Isso prova por que o controle atômico de JTI distribuído é mandatório para suportar 10.000+ jogadores.")
    print("Teste 4 (Contraexemplo) CONCLUÍDO COM SUCESSO.")