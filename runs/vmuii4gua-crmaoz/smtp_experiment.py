import socket
import threading
import time

class SimpleSMTPServer:
    def __init__(self, host='127.0.0.1', port=0):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))
        self.server_socket.listen(1)
        self.port = self.server_socket.getsockname()[1]
        self.is_running = False
        self.thread = None

    def start(self):
        self.is_running = True
        self.thread = threading.Thread(target=self._accept_connections)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.is_running = False
        self.server_socket.close()
        if self.thread:
            self.thread.join(timeout=1)

    def _accept_connections(self):
        while self.is_running:
            try:
                self.server_socket.settimeout(1.0)
                client_sock, _ = self.server_socket.accept()
                threading.Thread(target=self._handle_client, args=(client_sock,)).start()
            except socket.timeout:
                continue
            except Exception:
                break

    def _handle_client(self, client_sock):
        try:
            client_sock.sendall(b"220 localhost Simple SMTP Server Ready\r\n")
            
            # Estados da sessão SMTP
            state = "INIT"
            mail_from = None
            rcpt_to = []
            
            buffer = b""
            while self.is_running:
                data = client_sock.recv(1024)
                if not data:
                    break
                buffer += data
                
                while b"\r\n" in buffer:
                    line, buffer = buffer.split(b"\r\n", 1)
                    try:
                        line_str = line.decode('utf-8')
                    except UnicodeDecodeError:
                        client_sock.sendall(b"501 5.5.4 Invalid character encoding\r\n")
                        continue
                    
                    parts = line_str.split(" ", 1)
                    cmd = parts[0].upper()
                    args = parts[1] if len(parts) > 1 else ""
                    
                    if cmd == "HELO" or cmd == "EHLO":
                        state = "GREETED"
                        client_s = f"250 Hello {args}\r\n".encode('utf-8')
                        client_sock.sendall(client_s)
                        
                    elif cmd == "MAIL":
                        if state not in ("GREETED", "RCPT_TO"): # Permitir reset ou novos blocos se necessário
                            # RFC 5321: MAIL requer HELO prévio
                            client_sock.sendall(b"503 5.5.3 Bad sequence of commands (HELO first)\r\n")
                            continue
                        if args.upper().startswith("FROM:"):
                            mail_from = args[5:].strip()
                            state = "MAIL_FROM"
                            client_sock.sendall(b"250 2.1.0 Sender ok\r\n")
                        else:
                            client_sock.sendall(b"501 5.5.2 Syntax error in parameters\r\n")
                            
                    elif cmd == "RCPT":
                        if state not in ("MAIL_FROM", "RCPT_TO"):
                            client_sock.sendall(b"503 5.5.3 Bad sequence of commands\r\n")
                            continue
                        if args.upper().startswith("TO:"):
                            recipient = args[3:].strip()
                            rcpt_to.append(recipient)
                            state = "RCPT_TO"
                            client_sock.sendall(b"250 2.1.5 Recipient ok\r\n")
                        else:
                            client_sock.sendall(b"501 5.5.2 Syntax error in parameters\r\n")
                            
                    elif cmd == "DATA":
                        if state != "RCPT_TO":
                            client_sock.sendall(b"503 5.5.3 Bad sequence of commands\r\n")
                            continue
                        
                        client_sock.sendall(b"354 Start mail input; end with <CRLF>.<CRLF>\r\n")
                        
                        # Coleta dados até encontrar \r\n.\r\n
                        message_data = b""
                        while True:
                            if b"\r\n.\r\n" in buffer:
                                msg_part, buffer = buffer.split(b"\r\n.\r\n", 1)
                                message_data += msg_part
                                break
                            else:
                                chunk = client_sock.recv(1024)
                                if not chunk:
                                    break
                                buffer += chunk
                        
                        print(f"[SERVIDOR] Mensagem recebida de {mail_from} para {rcpt_to}. Tamanho do corpo: {len(message_data)} bytes")
                        client_sock.sendall(b"250 2.0.0 Message accepted for delivery\r\n")
                        # Reset de estado para múltiplos e-mails na mesma conexão
                        state = "GREETED"
                        mail_from = None
                        rcpt_to = []
                        
                    elif cmd == "QUIT":
                        client_sock.sendall(b"221 2.0.0 Bye\r\n")
                        break
                    elif cmd == "NOOP":
                        client_sock.sendall(b"250 2.0.0 OK\r\n")
                    elif cmd == "RSET":
                        state = "GREETED"
                        mail_from = None
                        rcpt_to = []
                        client_sock.sendall(b"250 2.0.0 Reset state\r\n")
                    else:
                        client_sock.sendall(b"500 5.5.2 Command not recognized\r\n")
        finally:
            client_sock.close()

# Bloco de Teste Automatizado
if __name__ == "__main__":
    server = SimpleSMTPServer()
    server.start()
    print(f"[TESTE] Servidor SMTP iniciado na porta {server.port}")
    
    try:
        # Conectando como Cliente SMTP
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', server.port))
        
        # 1. Ler banner de boas-vindas
        banner = s.recv(1024)
        print(f"<- {banner.decode().strip()}")
        assert banner.startswith(b"220")
        
        # 2. Testar violação de estado (enviar MAIL FROM sem HELO)
        s.sendall(b"MAIL FROM:<sender@test.com>\r\n")
        resp = s.recv(1024)
        print(f"<- {resp.decode().strip()}")
        assert resp.startswith(b"503") # Deve recusar por ordem incorreta
        
        # 3. Enviar HELO correto
        s.sendall(b"HELO client.local\r\n")
        resp = s.recv(1024)
        print(f"<- {resp.decode().strip()}")
        assert resp.startswith(b"250")
        
        # 4. Enviar MAIL FROM correto
        s.sendall(b"MAIL FROM:<alice@example.com>\r\n")
        resp = s.recv(1024)
        print(f"<- {resp.decode().strip()}")
        assert resp.startswith(b"250")
        
        # 5. Enviar RCPT TO correto
        s.sendall(b"RCPT TO:<bob@example.com>\r\n")
        resp = s.recv(1024)
        print(f"<- {resp.decode().strip()}")
        assert resp.startswith(b"250")
        
        # 6. Enviar DATA e corpo da mensagem
        s.sendall(b"DATA\r\n")
        resp = s.recv(1024)
        print(f"<- {resp.decode().strip()}")
        assert resp.startswith(b"354")
        
        msg = b"Subject: Test Email\r\nFrom: alice@example.com\r\nTo: bob@example.com\r\n\r\nHello, this is a test message.\r\n.\r\n"
        s.sendall(msg)
        resp = s.recv(1024)
        print(f"<- {resp.decode().strip()}")
        assert resp.startswith(b"250")
        
        # 7. Encerrar com QUIT
        s.sendall(b"QUIT\r\n")
        resp = s.recv(1024)
        print(f"<- {resp.decode().strip()}")
        assert resp.startswith(b"221")
        
        s.close()
        print("[TESTE] Todos os testes do protocolo SMTP passaram com sucesso!")
        
    finally:
        server.stop()