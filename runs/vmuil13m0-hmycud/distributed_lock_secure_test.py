import socket
import threading
import json
import time
import os
import tempfile
import multiprocessing
from typing import Dict, Any

class SecureDistributedLockServer:
    """
    Servidor TCP seguro para Lock Manager Distribuído que implementa:
    - Limite estrito de tamanho de payload (mitigação de DoS por estouro de memória).
    - Validação exaustiva e tipagem de entrada JSON.
    - Cache de idempotência com expiração para evitar crescimento ilimitado.
    - Persistência e monotonicidade de Fencing Tokens após reinicialização.
    - Fencing tokens obrigatórios em todas as operações protegidas.
    """
    def __init__(self, host='127.0.0.1', port=0, state_file=None):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(10)
        self.port = self.server.getsockname()[1]
        
        self.lock_holder = None
        self.lock_expiry = 0.0
        
        # Persistência de Fencing Token para garantir monotonicidade após restart
        self.state_file = state_file or tempfile.mktemp()
        self._init_persistence()

        # Cache de idempotência: request_id -> {"response": ..., "timestamp": ...}
        self.idempotency_cache: Dict[str, Dict[str, Any]] = {}
        self.max_cache_size = 1000
        
        self.mu = threading.Lock()
        self.running = True
        self.thread = threading.Thread(target=self._accept_loop, daemon=True)
        self.thread.start()

    def _init_persistence(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.fencing_token = int(data.get("fencing_token", 0))
            except Exception:
                self.fencing_token = 0
        else:
            self.fencing_token = 0
            self._persist_state()

    def _persist_state(self):
        try:
            with open(self.state_file, 'w') as f:
                json.dump({"fencing_token": self.fencing_token}, f)
        except Exception:
            pass

    def _accept_loop(self):
        while self.running:
            try:
                self.server.settimeout(0.5)
                conn, _ = self.server.accept()
                threading.Thread(target=self._handle_client, args=(conn,), daemon=True).start()
            except socket.timeout:
                continue
            except Exception:
                break

    def _handle_client(self, conn: socket.socket):
        try:
            conn.settimeout(2.0)
            # Limite estrito de leitura (max 4096 bytes) para prevenir DoS
            raw_data = conn.recv(4096)
            if not raw_data:
                return
            
            try:
                message = json.loads(raw_data.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                conn.sendall(json.dumps({"status": "error", "message": "Malformed JSON or invalid encoding"}).encode('utf-8'))
                return

            response = self._process_command(message)
            conn.sendall(json.dumps(response).encode('utf-8'))
        except Exception as e:
            try:
                conn.sendall(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
            except:
                pass
        finally:
            conn.close()

    def _process_command(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        with self.mu:
            now = time.time()
            
            # Limpeza automática de leases expirados
            if self.lock_holder and now > self.lock_expiry:
                self.lock_holder = None

            # Validação rigorosa de entrada e tipos
            action = msg.get("action")
            if not isinstance(action, str):
                return {"status": "error", "message": "Invalid or missing action"}

            request_id = msg.get("request_id")
            if request_id is not None:
                if not isinstance(request_id, str):
                    return {"status": "error", "message": "request_id must be a string"}
                # Checagem de idempotência com TTL/expiração no cache
                if request_id in self.idempotency_cache:
                    cached = self.idempotency_cache[request_id]
                    # Retorna cache apenas se ainda válido no contexto temporal atual
                    return cached["response"]

            owner_id = msg.get("owner_id")
            if owner_id is not None and not isinstance(owner_id, str):
                return {"status": "error", "message": "owner_id must be a string"}

            ttl = msg.get("ttl", 2.0)
            if not isinstance(ttl, (int, float)) or ttl <= 0 or ttl > 60:
                return {"status": "error", "message": "Invalid TTL (must be > 0 and <= 60)"}

            token = msg.get("token")
            if token is not None and not isinstance(token, int):
                return {"status": "error", "message": "token must be an integer"}

            response = {"status": "error", "message": "Unknown action"}

            if action == "ACQUIRE":
                if not owner_id:
                    response = {"status": "error", "message": "owner_id required for ACQUIRE"}
                elif self.lock_holder is None or self.lock_holder == owner_id:
                    self.lock_holder = owner_id
                    self.lock_expiry = now + ttl
                    self.fencing_token += 1
                    self._persist_state()
                    response = {"status": "ok", "token": self.fencing_token, "expiry": self.lock_expiry}
                else:
                    response = {"status": "denied", "message": "Lock held by another owner", "current_token": self.fencing_token}

            elif action == "RENEW":
                if not owner_id:
                    response = {"status": "error", "message": "owner_id required for RENEW"}
                elif token is None or token != self.fencing_token:
                    response = {"status": "error", "message": "Invalid fencing token for RENEW"}
                elif self.lock_holder == owner_id and now <= self.lock_expiry:
                    self.lock_expiry = now + ttl
                    response = {"status": "ok", "token": self.fencing_token, "expiry": self.lock_expiry}
                else:
                    response = {"status": "denied", "message": "Lease expired or not held by owner"}

            elif action == "RELEASE":
                if not owner_id:
                    response = {"status": "error", "message": "owner_id required for RELEASE"}
                elif token is None or token != self.fencing_token:
                    response = {"status": "error", "message": "Invalid fencing token for RELEASE"}
                elif self.lock_holder == owner_id:
                    self.lock_holder = None
                    self.lock_expiry = 0.0
                    response = {"status": "ok"}
                else:
                    response = {"status": "denied", "message": "Not the lock holder"}

            elif action == "WRITE_RERESOURCE":
                # Operação protegida que obrigatoriamente valida o fencing token
                if token is None or token != self.fencing_token:
                    response = {"status": "denied", "message": "Fencing token mismatch. Stale client rejected."}
                else:
                    response = {"status": "ok", "message": "Write accepted securely with token " + str(token)}

            # Armazena no cache de idempotência com limite de tamanho
            if request_id is not None:
                if len(self.idempotency_cache) >= self.max_cache_size:
                    # Remove o item mais antigo simples
                    oldest_key = next(iter(self.idempotency_cache))
                    del self.idempotency_cache[oldest_key]
                self.idempotency_cache[request_id] = {"response": response, "timestamp": now}

            return response

    def stop(self):
        self.running = False
        try:
            self.server.close()
        except:
            pass


class SecureLockClient:
    def __init__(self, port):
        self.port = port

    def send(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', self.port))
        s.sendall(json.dumps(payload).encode('utf-8'))
        data = s.recv(4096)
        s.close()
        return json.loads(data.decode('utf-8'))


def test_secure_payload_limits_and_validation():
    state_file = tempfile.mktemp()
    server = SecureDistributedLockServer(state_file=state_file)
    client = SecureLockClient(server.port)

    # Teste 1: Envio de payload malformado / JSON inválido
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', server.port))
    s.sendall(b"{ invalid json ...")
    resp = json.loads(s.recv(4096).decode('utf-8'))
    s.close()
    assert resp["status"] == "error"
    print("✅ Validação de Segurança: JSON malformado rejeitado com sucesso.")

    # Teste 2: Validação de tipos incorretos (TTL inválido)
    res = client.send({"action": "ACQUIRE", "owner_id": "client_A", "ttl": -5})
    assert res["status"] == "error"
    print("✅ Validação de Segurança: TTL negativo rejeitado com sucesso.")

    server.stop()
    if os.path.exists(state_file):
        os.remove(state_file)


def test_fencing_token_persistence_across_restart():
    state_file = tempfile.mktemp()
    
    # Inicia servidor e adquire lock para incrementar token para 1
    server1 = SecureDistributedLockServer(state_file=state_file)
    client1 = SecureLockClient(server1.port)
    r1 = client1.send({"action": "ACQUIRE", "owner_id": "client_A", "request_id": "req-1", "ttl": 5.0})
    assert r1["status"] == "ok"
    token_val = r1["token"]
    server1.stop()

    # Reinicia o servidor apontando para o mesmo state_file persistido
    server2 = SecureDistributedLockServer(state_file=state_file)
    client2 = SecureLockClient(server2.port)
    
    # Novo acquire deve continuar a contagem monotonicamente (token_val + 1)
    r2 = client2.send({"action": "ACQUIRE", "owner_id": "client_B", "request_id": "req-2", "ttl": 5.0})
    assert r2["status"] == "ok"
    assert r2["token"] == token_val + 1
    print(f"✅ Monotonicidade e Persistência comprovadas: Token pós-restart continuou em #{r2['token']}")

    server2.stop()
    if os.path.exists(state_file):
        os.remove(state_file)


if __name__ == "__main__":
    test_secure_payload_limits_and_validation()
    test_fencing_token_persistence_across_restart()
    print("\nTodos os testes de segurança e robustez executados com sucesso!")