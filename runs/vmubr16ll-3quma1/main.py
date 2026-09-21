path=game_auth_experiment.py
import time
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

# ==========================================
# 1. SETUP DE CRIPTOGRAFIA (Chaves Assimétricas)
# ==========================================
# Geramos um par de chaves RSA para simular o Auth Server (Privada) 
# e o Game Server (Pública).
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)
public_key = private_key.public_key()

# Serialização para uso nas bibliotecas de JWT
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
        "nbf": now,
        "exp": now + 300, # Sessão válida por 5 minutos
        "iss": "game-auth-provider"
    }
    return jwt.encode(payload, private_pem, algorithm="RS256")

# ==========================================
# 3. COMPONENTE: GAME SERVER (Validador)
# ==========================================
class GameServerSessionManager:
    def __init__(self):
        # Simula o armazenamento em memória de JTIs ativos para prevenir Replay Attacks
        self.active_jtis = set()
        self.revoked_jtis = set()

    def authenticate_player_handshake(self, token: str) -> dict:
        """
        Valida a assinatura criptográfica, expiração e integridade do token,
        além de garantir proteção contra replay attacks via verificação de jti.
        Deve executar em < 200ms (na prática, validação local leva < 5ms).
        """
        start_time = time.time()
        
        try:
            # 1. Validação Criptográfica e de Claims Temporais (exp, nbf, iat)
            payload = jwt.decode(
                token, 
                public_pem, 
                algorithms=["RS256"],
                options={"verify_exp": True, "verify_nbf": True}
            )
        except jwt.ExpiredSignatureError:
            raise PermissionError("Token expirado.")
        except jwt.InvalidTokenError as e:
            raise PermissionError(f"Token inválido ou adulterado: {e}")

        jti = payload.get("jti")
        sub = payload.get("sub")

        # 2. Proteção contra Replay Attack (verificando se o jti já foi consumido ou invalidado)
        if jti in self.revoked_jtis or jti in self.active_jtis:
            raise PermissionError("Replay Attack detectado: JTI de sessão já utilizado ou ativo concorrentemente.")

        # Registra o JTI como ativo para esta sessão
        self.active_jtis.add(jti)
        
        elapsed_ms = (time.time() - start_time) * 1000
        print(f"[GameServer] Autenticação bem-sucedida para o jogador {sub} em {elapsed_ms:.2f} ms")
        
        return {"status": "authenticated", "player_id": sub, "jti": jti}

    def disconnect_player(self, jti: str):
        """Move o JTI de ativos para revogados ao encerrar a partida/conexão."""
        if jti in self.active_jtis:
            self.active_jtis.remove(jti)
            self.revoked_jtis.add(jti)

# ==========================================
# 4. EXECUÇÃO DOS TESTES E DEMONSTRAÇÃO
# ==========================================
if __name__ == "__main__":
    server_manager = GameServerSessionManager()

    print("--- TESTE 1: Fluxo Normal de Conexão ---")
    token_valido = issue_game_session_token(player_id="player_123", session_jti="session-unique-abc-999")
    
    # Simula handshake bem-sucedido
    session_info = server_manager.authenticate_player_handshake(token_valido)
    assert session_info["player_id"] == "player_123"
    print("Teste 1 APROVADO: Conexão inicial estabelecida com sucesso.\n")

    print("--- TESTE 2: Ataque de Repetição (Replay Attack) com mesmo JTI ---")
    try:
        # O atacante tenta reutilizar exatamente o mesmo token capturado na rede
        server_manager.authenticate_player_handshake(token_valido)
        raise AssertionError("Deveria ter falhado por replay attack!")
    except PermissionError as e:
        print(f"Defesa bem-sucedida contra Replay: {e}")
        print("Teste 2 APROVADO: Replay attack bloqueado com sucesso.\n")

    print("--- TESTE 3: Contraexemplo de Falha (Validação ingênua sem verificação de jti) ---")
    # Se o servidor validasse APENAS a assinatura matemática sem checar estado de sessão (JTI),
    # um token válido roubado poderia ser reutilizado infinitamente dentro da janela de 5 minutos.
    # Vamos demonstrar o comportamento inseguro se omitirmos o controle de JTI:
    
    # Servidor Inseguro hipotético que ignora replay check:
    def insecure_naive_validation(token):
        # Apenas decodifica (assinatura válida)
        return jwt.decode(token, public_pem, algorithms=["RS256"])

    # Atacante reutiliza o token válido 10 segundos depois:
    payload_reutilizado = insecure_naive_validation(token_valido)
    print(f"[AVISO DE SEGURANÇA] Na abordagem ingênua, o token do player {payload_reutilizado['sub']} "
          f"seria aceito novamente porque a assinatura RSA ainda é matematicamente válida!")
    print("Isso prova por que a verificação de estado do `jti` no Servidor de Jogo é mandatório.")
    print("Teste 3 (Contraexemplo) CONCLUÍDO COM SUCESSO.")