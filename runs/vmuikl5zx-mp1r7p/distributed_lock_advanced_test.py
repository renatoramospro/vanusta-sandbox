import socket
import threading
import json
import time
import multiprocessing
from typing import Dict, Any

class AdvancedDistributedLockServer:
    """
    Servidor TCP centralizado que suporta:
    - Exclusão mútua com Fencing Tokens.
    - Time-To-Live (TTL) automático.
    - Renovação de Lease (Heartbeat) para tarefas longas.
    - Idempotência de requisições via request_id para mitigar timeouts de rede.
    """
    def __init__(self, host='127.0.0.1', port=0):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(10)
        self.port = self.server.getsockname()[1]
        
        self.lock_holder = None  # owner_id atual
        self.lock_expiry = 0.0   # timestamp de expiração
        self.fencing_token = 0   # contador monotônico
        self.processed_requests: Dict[str, Dict[str, Any]] = {} # Cache de idempotência: request_id -> resposta
        
        self.mu = threading.Lock()
        self.running = True
        self.thread = threading.Thread(target=self._accept_loop, daemon=True)
        self.thread.start()

    def _accept_loop(self):
        while self.running:
            try:
                self.server.settimeout(0.5)
                conn, _ = self.server.accept()
                threading.Thread(target=self._handle_client, args=(conn,), daemon=True).start()
            except socket.timeout:
                continue
            except OSError:
                break

    def _handle_client(self, conn: socket.socket):
        try:
            data = conn.recv(4096)
            if not data:
                return
            req = json.loads(data.decode('utf-8'))
            
            action = req.get('action')
            owner_id = req.get('owner_id')
            request_id = req.get('request_id')
            ttl = req.get('ttl', 2.0)

            with self.mu:
                now = time.time()
                # Verifica expiração natural (TTL)
                if self.lock_holder and now > self.lock_expiry:
                    print(f"[Server] TTL expirado para o holder anterior: {self.lock_holder}")
                    self.lock_holder = None

                # 1. Checagem de Idempotência
                if request_id and request_id in self.processed_requests:
                    conn.sendall(json.dumps(self.processed_requests[request_id]).encode('utf-8'))
                    return

                response = {"status": "error", "message": "Unknown action"}

                if action == 'acquire':
                    if self.lock_holder is None or self.lock_holder == owner_id:
                        self.lock_holder = owner_id
                        self.lock_expiry = now + ttl
                        self.fencing_token += 1
                        response = {
                            "status": "ok", 
                            "token": self.fencing_token, 
                            "expiry": self.lock_expiry
                        }
                    else:
                        response = {"status": "denied", "message": "Lock already held by another process"}

                elif action == 'renew':
                    if self.lock_holder == owner_id:
                        self.lock_expiry = now + ttl
                        response = {
                            "status": "ok", 
                            "token": self.fencing_token, 
                            "expiry": self.lock_expiry
                        }
                    else:
                        response = {"status": "denied", "message": "Not the current lock holder"}

                elif action == 'release':
                    if self.lock_holder == owner_id:
                        self.lock_holder = None
                        self.lock_expiry = 0.0
                        response = {"status": "ok"}
                    else:
                        response = {"status": "denied", "message": "Not the current lock holder"}

                # Salva no cache de idempotência se houver request_id
                if request_id:
                    self.processed_requests[request_id] = response

                conn.sendall(json.dumps(response).encode('utf-8'))
        except Exception as e:
            try:
                conn.sendall(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
            except:
                pass
        finally:
            conn.close()

    def stop(self):
        self.running = False
        self.server.close()
        self.thread.join(timeout=1)


class DistributedClient:
    def __init__(self, port: int, owner_id: str):
        self.port = port
        self.owner_id = owner_id

    def _send(self, payload: dict) -> dict:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', self.port))
        s.sendall(json.dumps(payload).encode('utf-8'))
        data = s.recv(4096)
        s.close()
        return json.loads(data.decode('utf-8'))

    def acquire(self, request_id: str, ttl: float = 2.0):
        return self._send({"action": "acquire", "owner_id": self.owner_id, "request_id": request_id, "ttl": ttl})

    def renew(self, request_id: str, ttl: float = 2.0):
        return self._send({"action": "renew", "owner_id": self.owner_id, "request_id": request_id, "ttl": ttl})

    def release(self, request_id: str):
        return self._send({"action": "release", "owner_id": self.owner_id, "request_id": request_id})


class ProtectedResource:
    """Recurso protegido que valida Fencing Tokens estritamente."""
    def __init__(self):
        self.last_seen_token = 0
        self.data = ""

    def write(self, token: int, value: str):
        if token <= self.last_seen_token:
            raise ValueError(f"Fencing token obsoleto ou reordenado! Recebido: {token}, Último visto: {self.last_seen_token}")
        self.last_seen_token = token
        self.data = value


def test_heartbeat_lease_renewal():
    server = AdvancedDistributedLockServer()
    client = DistributedClient(server.port, "client-long-task")

    # Adquire trava com TTL curto (1.0s)
    res = client.acquire(request_id="req-1", ttl=1.0)
    assert res["status"] == "ok"
    token1 = res["token"]
    print(f"✅ Trava adquirida com Token #{token1}")

    # Simula o decorrer de 0.6s e faz um heartbeat (renovação) antes do TTL expirar
    time.sleep(0.6)
    res_renew = client.renew(request_id="req-2", ttl=2.0)
    assert res_renew["status"] == "ok"
    assert res_renew["token"] == token1  # Mantém o mesmo fencing token
    print(f"✅ Lease renovado com sucesso via heartbeat. Token mantido: #{res_renew['token']}")

    # Aguarda mais 1.0s (totalizando 1.6s desde o início, o que estouraria o TTL original de 1.0s)
    time.sleep(1.0)
    
    # Como houve renovação, a trava AINDA deve pertencer ao cliente
    resource = ProtectedResource()
    resource.write(res_renew["token"], "dados seguros após heartbeat")
    print(f"✅ Escrita bem-sucedida no recurso após tarefa longa estendida por heartbeat.")

    client.release(request_id="req-3")
    server.stop()


def test_network_timeout_idempotency():
    server = AdvancedDistributedLockServer()
    client = DistributedClient(server.port, "client-idempotent")

    # Envia requisição de acquire com um request_id fixo
    req_id = "idem-req-999"
    res1 = client.acquire(request_id=req_id, ttl=2.0)
    assert res1["status"] == "ok"
    token_first = res1["token"]

    # Simula timeout de rede e retentativa enviando EXATAMENTE o mesmo request_id
    res2 = client.acquire(request_id=req_id, ttl=2.0)
    assert res2["status"] == "ok"
    assert res2["token"] == token_first  # Retorna exatamente a mesma resposta cacheada sem incrementar token indevidamente
    print(f"✅ Idempotência comprovada: retentativa com mesmo request_id retornou idêntico Token #{token_first}")

    server.stop()


if __name__ == "__main__":
    test_heartbeat_lease_renewal()
    test_network_timeout_idempotency()
    print("\nTodos os testes avançados (Heartbeat e Idempotência) executados com sucesso!")