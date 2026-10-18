import time
import hashlib
import hmac
import os
import json

# --- Simulação do Protocolo Kerberos (AS, TGS, Service, Delegation) ---

class MockKDC:
    def __init__(self):
        # Base de dados simulada de usuários e suas chaves secretas (derivadas de senhas)
        self.user_keys = {
            "alice": hashlib.sha256("senha_super_secreta_alice".encode()).digest()
        }
        # Chave secreta mestre do TGS e do Serviço
        self.tgs_secret = os.urandom(32)
        self.service_secret = os.urandom(32)

    def authenticate_as(self, username, client_timestamp):
        """Passo 1: AS-REQ / AS-REP (Autenticação e emissão de TGT)"""
        if username not in self.user_keys:
            raise ValueError("Usuário desconhecido")
        
        # Verifica se o timestamp está dentro da janela de validade (previne replay simples)
        current_time = time.time()
        if abs(current_time - client_timestamp) > 300: # 5 minutos de tolerância
            raise PermissionError("Timestamp inválido (possível ataque de replay)")

        # Cria o TGT (Ticket-Granting Ticket) cifrado com a chave do TGS
        tgt_data = {
            "username": username,
            "expiration": current_time + 3600, # 1 hora de validade
            "forwardable": True
        }
        tgt_json = json.dumps(tgt_data).encode()
        
        # Assina o TGT com a chave do TGS para garantir integridade
        tgt_signature = hmac.new(self.tgs_secret, tgt_json, hashlib.sha256).digest()
        tgt = {"data": tgt_json.hex(), "sig": tgt_signature.hex()}

        # Cria a chave de sessão para o cliente se comunicar com o TGS
        session_key = os.urandom(32)
        
        return {
            "tgt": tgt,
            "session_key": session_key.hex(),
            "expiration": tgt_data["expiration"]
        }

    def request_tgs(self, tgt, service_name, client_session_key_hex):
        """Passo 2: TGS-REQ / TGS-REP (Emissão de Service Ticket com Delegação)"""
        # Valida o TGT
        tgt_json = bytes.fromhex(tgt["data"])
        expected_sig = hmac.new(self.tgs_secret, tgt_json, hashlib.sha256).digest()
        
        if not hmac.compare_digest(expected_sig, bytes.fromhex(tgt["sig"])):
            raise PermissionError("TGT adulterado ou inválido!")

        tgt_data = json.loads(tgt_json.decode())
        if time.time() > tgt_data["expiration"]:
            raise PermissionError("TGT expirado!")

        # Emite o Service Ticket (ST) com suporte a delegação (forwardable)
        st_data = {
            "username": tgt_data["username"],
            "service": service_name,
            "forwardable": tgt_data["forwardable"],
            "expiration": time.time() + 1800 # 30 minutos
        }
        st_json = json.dumps(st_data).encode()
        st_signature = hmac.new(self.service_secret, st_json, hashlib.sha256).digest()
        
        return {
            "service_ticket": {"data": st_json.hex(), "sig": st_signature.hex()},
            "service": service_name
        }

# --- Testes Automatizados e Carga ---

def test_kerberos_authentication_and_delegation():
    kdc = MockKDC()
    username = "alice"
    
    print("[*] Iniciando teste de autenticação Kerberos e delegação...")
    
    # 1. Autenticação no AS
    t0 = time.time()
    as_response = kdc.authenticate_as(username, t0)
    print(f"[Sucesso] TGT obtido para {username}. Chave de sessão gerada com sucesso.")
    
    # 2. Solicitação de Service Ticket ao TGS com Delegação
    st_response = kdc.request_tgs(as_response["tgt"], "api_servico_backend", as_response["session_key"])
    print(f"[Sucesso] Service Ticket obtido para o serviço '{st_response['service']}' com flag forwardable=True.")
    
    assert st_response["service_ticket"] is not None
    print("[Passou] Teste unitário de fluxo completo concluído.")

def test_contraexemplo_ticket_adulterado():
    kdc = MockKDC()
    as_response = kdc.authenticate_as("alice", time.time())
    
    # Adulterando o TGT propositalmente
    tgt_falso = as_response["tgt"].copy()
    tgt_falso["data"] = json.dumps({"username": "hacker", "expiration": time.time() + 3600, "forwardable": True}).encode().hex()
    
    try:
        kdc.request_tgs(tgt_falso, "api_servico_backend", as_response["session_key"])
        raise AssertionError("Deveria ter falhado por adulteração!")
    except PermissionError as e:
        print(f"[Contraexemplo Capturado com Sucesso] O KDC rejeitou o TGT adulterado: {e}")

def test_carga_kerberos():
    kdc = MockKDC()
    total_requisicoes = 1000
    sucessos = 0
    latencias = []

    print(f"[*] Iniciando teste de carga com {total_requisicoes} requisições...")
    inicio_carga = time.time()

    for _ in range(total_requisicoes):
        t_inicio_req = time.time()
        try:
            # Simula fluxo completo de obtenção de TGT e ST sob carga
            as_resp = kdc.authenticate_as("alice", time.time())
            kdc.request_tgs(as_resp["tgt"], "servico_alvo", as_resp["session_key"])
            sucessos += 1
        except Exception:
            pass
        latencias.append((time.time() - t_inicio_req) * 1000) # em milissegundos

    fim_carga = time.time()
    taxa_sucesso = (sucessos / total_requisicoes) * 100
    latencia_media = sum(latencias) / len(latencias)

    print(f"[%] Resultados do Teste de Carga:")
    print(f"    - Total de Requisições: {total_requisicoes}")
    print(f"    - Taxa de Sucesso: {taxa_sucesso:.2f}%")
    print(f"    - Latência Média: {latencia_media:.2f} ms")

    # Critérios de Sucesso Revisados pelo Arquiteto: Taxa de sucesso >= 99% e latência média < 200ms
    assert taxa_sucesso >= 99.0, f"Taxa de sucesso abaixo do esperado: {taxa_sucesso}%"
    assert latencia_media < 200.0, f"Latência média acima do limite de 200ms: {latencia_media}ms"
    print("[Passou] Teste de carga aprovado dentro dos critérios rigorosos!")

if __name__ == "__main__":
    test_kerberos_authentication_and_delegation()
    test_contraexemplo_ticket_adulterado()
    test_carga_kerberos()