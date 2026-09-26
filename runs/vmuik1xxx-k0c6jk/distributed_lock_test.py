import socket
import threading
import json
import time
import multiprocessing
from typing import Dict, Any

class DistributedLockServer:
    """
    Simula um Serviço de Lock Distribuído centralizado (estilo Chubby/Redis single-node coordinator)
    ouvindo em um socket TCP local, atendendo múltiplos processos concorrentes na rede.
    """
    def __init__(self, host='127.0.0.1', port=0):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(128)
        self.port = self.server.getsockname()[1]
        
        self._storage: Dict[str, Dict] = {} # resource_id -> {owner_id, expires_at, fencing_token}
        self._global_token_counter = 0
        self._lock = threading.Lock()
        self._is_running = True
        self._thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._thread.start()

    def _accept_loop(self):
        while self._is_running:
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
            data = conn.recv(4096)
            if not data:
                return
            request = json.loads(data.decode('utf-8'))
            response = self._process_request(request)
            conn.sendall(json.dumps(response).encode('utf-8'))
        except Exception as e:
            try:
                conn.sendall(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
            except:
                pass
        finally:
            conn.close()

    def _process_request(self, req: Dict[str, Any]) -> Dict[str, Any]:
        action = req.get("action")
        resource_id = req.get("resource_id")
        owner_id = req.get("owner_id")
        ttl = req.get("ttl", 2.0)

        with self._lock:
            now = time.time()
            current = self._storage.get(resource_id)

            # Verifica expiração por TTL (Lease expiration)
            if current and current["expires_at"] <= now:
                print(f"[Server] ⏰ TTL expirado para recurso '{resource_id}' (antigo dono: {current['owner_id']})")
                self._storage.pop(resource_id, None)
                current = None

            if action == "acquire":
                if current:
                    return {"status": "denied", "reason": "locked"}
                
                self._global_token_counter += 1
                token = self._global_token_counter
                self._storage[resource_id] = {
                    "owner_id": owner_id,
                    "expires_at": now + ttl,
                    "fencing_token": token
                }
                print(f"[Server] 🔒 Concedido '{resource_id}' para '{owner_id}' com Fencing Token #{token}")
                return {"status": "success", "fencing_token": token}

            elif action == "release":
                if not current or current["owner_id"] != owner_id:
                    return {"status": "denied", "reason": "not_owner"}
                
                self._storage.pop(resource_id, None)
                print(f"[Server] 🔓 Liberado '{resource_id}' por '{owner_id}'")
                return {"status": "success"}

        return {"status": "error", "reason": "unknown_action"}

    def stop(self):
        self._is_running = False
        try:
            self.server.close()
        except:
            pass


class DistributedLockClient:
    """Cliente que se comunica via TCP com o Lock Server."""
    def __init__(self, host: str, port: int, owner_id: str):
        self.host = host
        self.port = port
        self.owner_id = owner_id

    def _send(self, payload: dict) -> dict:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        s.sendall(json.dumps(payload).encode('utf-8'))
        resp = json.loads(s.recv(4096).decode('utf-8'))
        s.close()
        return resp

    def acquire(self, resource_id: str, ttl: float = 2.0):
        res = self._send({"action": "acquire", "resource_id": resource_id, "owner_id": self.owner_id, "ttl": ttl})
        if res.get("status") == "success":
            return res.get("fencing_token")
        return None

    def release(self, resource_id: str):
        res = self._send({"action": "release", "resource_id": resource_id, "owner_id": self.owner_id})
        return res.get("status") == "success"


def worker_process(port, client_name, results_dict):
    """Função executada por processos multiprocesso independentes."""
    client = DistributedLockClient('127.0.0.1', port, client_name)
    token = client.acquire("recurso_critico", ttl=1.0)
    if token is not None:
        results_dict[client_name] = {"acquired": True, "token": token}
        # Simula trabalho na seção crítica
        time.sleep(0.3)
        client.release("recurso_critico")
    else:
        results_dict[client_name] = {"acquired": False}


def test_multiprocess_mutual_exclusion():
    server = DistributedLockServer()
    manager = multiprocessing.Manager()
    results = manager.dict()

    # Dispara dois processos concorrentes independentes tentando pegar a trava ao mesmo tempo
    p1 = multiprocessing.Process(target=worker_process, args=(server.port, "Processo-A", results))
    p2 = multiprocessing.Process(target=worker_process, args=(server.port, "Processo-B", results))

    p1.start()
    p2.start()
    p1.join()
    p2.join()
    server.stop()

    # Apenas um deve ter conseguido adquirir com sucesso
    acquired_count = sum(1 for k, v in results.items() if v.get("acquired"))
    assert acquired_count == 1, f"Violação de exclusão mútua! Adquisições: {results}"
    print(f"✅ Exclusão mútua multiprocesso validada com sucesso! Resultados: {dict(results)}")


def test_fencing_token_safety_against_paused_client():
    """
    Demonstra a segurança contra o equívoco de cliente pausado usando Fencing Tokens.
    Se o Processo A expira por pausa, o Processo B assume com um token maior.
    Se o Processo A tentar escrever no armazenamento usando seu token antigo, o recurso rejeita.
    """
    server = DistributedLockServer()
    clientA = DistributedLockClient('127.0.0.1', server.port, "Cliente-A")
    clientB = DistributedLockClient('127.0.0.1', server.port, "Cliente-B")

    # 1. Cliente A adquire a trava (Token #1)
    token_a = clientA.acquire("recurso_fencing", ttl=0.4)
    assert token_a == 1
    print(f"Cliente A adquiriu com Token #{token_a}")

    # 2. Cliente A sofre uma pausa longa (excede o TTL de 0.4s)
    print("Cliente A pausado simulando GC/Network stall...")
    time.sleep(0.6)

    # 3. TTL expira, Cliente B adquire a trava legitimamente (Token #2)
    token_b = clientB.acquire("recurso_fencing", ttl=2.0)
    assert token_b == 2
    print(f"Cliente B adquiriu com Token #{token_b} após expiração legítima.")

    # 4. Simulação da validação de Fencing Token no recurso protegido:
    # O recurso armazena o último fencing token aceito.
    class ProtectedResourceMock:
        def __init__(self):
            self.last_fencing_token = 0
            self.data = None

        def write(self, token: int, value: str):
            if token <= self.last_fencing_token:
                raise ValueError(f"Stale fencing token {token} rejeitado! (Último válido: {self.last_fencing_token})")
            self.last_fencing_token = token
            self.data = value

    resource = ProtectedResourceMock()

    # Cliente B escreve com sucesso (Token 2)
    resource.write(token_b, "dados do Cliente B")
    print("✅ Cliente B escreveu com sucesso usando o Token #2.")

    # Cliente A acorda atrasado e tenta escrever com seu token antigo (Token 1)
    try:
        resource.write(token_a, "dados desatualizados do Cliente A")
        assert False, "Deveria ter rejeitado o token obsoleto!"
    except ValueError as e:
        print(f"🛡️ Fencing Token validado com sucesso: {e}")

    server.stop()


if __name__ == "__main__":
    test_multiprocess_mutual_exclusion()
    test_fencing_token_safety_around_pauses = test_fencing_token_safety_against_paused_client()
    print("\nTodos os testes distribuídos multiprocesso e de fencing tokens executados com sucesso!")