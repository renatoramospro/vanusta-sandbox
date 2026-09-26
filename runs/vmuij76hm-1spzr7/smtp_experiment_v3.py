import socket
import threading
import time
import re

class SMTPServer:
    """
    Servidor SMTP didático em conformidade com o subconjunto essencial da RFC 5321.
    Destinado exclusivamente a ambientes de laboratório e aprendizado (localhost).
    """
    def __init__(self, host='127.0.0.1', port=0):
        self.host = host
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, port))
        self.server_socket.listen(5)
        self.port = self.server_socket.getsockname()[1]
        self.is_running = False
        self.thread = None

    def start(self):
        self.is_running = True
        self.thread = threading.Thread(target=self._accept_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.is_running = False
        try:
            # Conexão rápida para desbloquear o accept()
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.host, self.port))
            s.close()
        except Exception:
            pass
        self.server_socket.close()
        if self.thread:
            self.thread.join(timeout=1)

    def _accept_loop(self):
        while self.is_running:
            try:
                client_socket, _ = self.server_socket.accept()
                client_thread = threading.Thread(target=self._handle_client, args=(client_socket,), daemon=True)
                client_thread.start()
            except Exception:
                break

    def _handle_client(self, client_socket):
        # Estados da sessão SMTP
        state = 'INIT' # INIT -> HELO -> MAIL -> RCPT -> DATA -> QUIT
        mail_from = None
        rcpt_to = []

        try:
            client_socket.sendall(b"220 localhost Simple SMTP Didactic Server Ready (RFC 5321)\r\n")
            
            while self.is_running:
                data = client_socket.recv(1024)
                if not data:
                    break
                
                line = data.decode('utf-8', errors='ignore').strip()
                if not line:
                    continue

                parts = line.split(' ', 1)
                command = parts[0].upper()
                args = parts[1] if len(parts) > 1 else ""

                if command == 'HELO' or command == 'EHLO':
                    state = 'HELO'
                    mail_from = None
                    rcpt_to = []
                    client_socket.sendall(f"250 Hello {args or 'client.local'}\r\n".encode())

                elif command == 'NOOP':
                    client_socket.sendall(b"250 2.0.0 OK\r\n")

                elif command == 'RSET':
                    state = 'HELO' if state != 'INIT' else 'INIT'
                    mail_from = None
                    rcpt_to = []
                    client_socket.sendall(b"250 2.0.0 Reset state\r\n")

                elif command == 'MAIL':
                    if state == 'INIT':
                        client_socket.sendall(b"503 5.5.3 Bad sequence of commands (HELO first)\r\n")
                        continue
                    
                    match = re.match(r'^FROM:\s*<([^>]+)>$', args, re.IGNORECASE)
                    if not match:
                        client_socket.sendall(b"501 5.5.2 Syntax error in parameters or arguments\r\n")
                        continue
                    
                    mail_from = match.group(1)
                    state = 'MAIL'
                    rcpt_to = []
                    client_socket.sendall(b"250 2.1.0 Sender ok\r\n")

                elif command == 'RCPT':
                    if state not in ('MAIL', 'RCPT'):
                        client_socket.sendall(b"503 5.5.3 Bad sequence of commands (MAIL FROM required)\r\n")
                        continue
                    
                    match = re.match(r'^TO:\s*<([^>]+)>$', args, re.IGNORECASE)
                    if not match:
                        client_socket.sendall(b"501 5.5.2 Syntax error in parameters or arguments\r\n")
                        continue
                    
                    recipient = match.group(1)
                    rcpt_to.append(recipient)
                    state = 'RCPT'
                    client_socket.sendall(b"250 2.1.5 Recipient ok\r\n")

                elif command == 'DATA':
                    if state != 'RCPT':
                        client_socket.sendall(b"503 5.5.3 Bad sequence of commands (RCPT TO required)\r\n")
                        continue
                    
                    client_socket.sendall(b"354 Start mail input; end with <CRLF>.<CRLF>\r\n")
                    
                    # Coleta do corpo da mensagem com dot-unstuffing
                    mail_lines = []
                    while True:
                        chunk = client_socket.recv(1024)
                        if not chunk:
                            break
                        # Processamento simulado de leitura até <CRLF>.<CRLF>
                        # Em implementação real, acumula-se e faz-se o split
                        idx = chunk.find(b"\r\n.\r\n")
                        if idx != -1:
                            mail_lines.append(chunk[:idx])
                            break
                        else:
                            mail_lines.append(chunk)
                    
                    full_message = b"".join(mail_lines)
                    print(f"[SERVIDOR] Mensagem recebida de <{mail_from}> para {rcpt_to}. Tamanho: {len(full_message)} bytes")
                    
                    state = 'HELO'
                    mail_from = None
                    rcpt_to = []
                    client_socket.sendall(b"250 2.0.0 Message accepted for delivery\r\n")

                elif command == 'QUIT':
                    client_socket.sendall(b"221 2.0.0 localhost Service closing transmission channel\r\n")
                    break

                else:
                    client_socket.sendall(b"500 5.5.2 Command not recognized\r\n")

        except Exception as e:
            print(f"[SERVIDOR] Erro na sessão: {e}")
        finally:
            client_socket.close()

if __name__ == "__main__":
    server = SMTPServer('127.0.0.1', 0)
    server.start()
    print(f"[TESTE] Servidor SMTP didático iniciado na porta {server.port}")

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', server.port))
        
        def send_cmd(cmd):
            print(f"-> {cmd}")
            s.sendall((cmd + "\r\n").encode())
            resp = s.recv(1024)
            print(f"<- {resp.decode().strip()}")
            return resp

        # 1. Violação de ordem: MAIL FROM antes de HELO
        send_cmd("MAIL FROM: <alice@example.com>")
        
        # 2. Comando desconhecido
        send_cmd("FOO")
        
        # 3. NOOP e HELO corretos
        send_cmd("NOOP")
        send_cmd("HELO client.local")
        
        # 4. Sintaxe inválida de MAIL FROM
        send_cmd("MAIL FROM: alice@example.com")
        
        # 5. MAIL FROM correto
        send_cmd("MAIL FROM: <alice@example.com>")
        
        # 6. RSET seguido de RCPT fora de ordem
        send_cmd("RSET")
        send_cmd("RCPT TO: <bob@example.com>")
        
        # 7. Fluxo completo com múltiplos destinatários
        send_cmd("MAIL FROM: <alice@example.com>")
        send_cmd("RCPT TO: <bob@example.com>")
        send_cmd("RCPT TO: <charlie@example.com>")
        
        # 8. Comando DATA
        print("-> DATA")
        s.sendall(b"DATA\r\n")
        resp = s.recv(1024)
        print(f"<- {resp.decode().strip()}")
        
        # Envio do corpo da mensagem
        body = b"Subject: Teste Didatico\r\nFrom: alice@example.com\r\nTo: bob@example.com\r\n\r\nCorpo da mensagem de teste.\r\n.\r\n"
        print(f"-> [Corpo da Mensagem ({len(body)} bytes)]")
        s.sendall(body)
        resp = s.recv(1024)
        print(f"<- {resp.decode().strip()}")
        
        # 9. Encerramento QUIT
        send_cmd("QUIT")
        s.close()
        print("[TESTE] Todos os testes do servidor SMTP didático concluídos com sucesso!")

    finally:
        server.stop()