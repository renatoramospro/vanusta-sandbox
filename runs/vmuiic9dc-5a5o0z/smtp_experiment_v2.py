import socket
import threading
import time
import re

class SMTPServer:
    def __init__(self, host='127.0.0.1', port=0):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))
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
            # Conexão rápida para destravar o accept se necessário
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(('127.0.0.1', self.port))
            s.close()
        except:
            pass
        self.server_socket.close()

    def _accept_loop(self):
        while self.is_running:
            try:
                client_sock, _ = self.server_socket.accept()
                threading.Thread(target=self._handle_client, args=(client_sock,), daemon=True).start()
            except:
                break

    def _handle_client(self, client_sock):
        # Estados: INIT, GREETED, MAIL, RCPT, DATA, QUIT
        state = 'INIT'
        mail_from = None
        rcpt_to = []
        
        client_sock.sendall(b"220 localhost Simple SMTP Server Ready (RFC 5321)\r\n")
        
        buffer = b""
        while self.is_running:
            data = client_sock.recv(1024)
            if not data:
                break
            buffer += data
            
            while b"\r\n" in buffer:
                line, buffer = buffer.split(b"\r\n", 1)
                line_str = line.decode('utf-8', errors='ignore').strip()
                if not line_str:
                    continue
                
                parts = line_str.split(' ', 1)
                cmd = parts[0].upper()
                args = parts[1] if len(parts) > 1 else ""
                
                # NOOP é permitido em qualquer estado após conexão
                if cmd == 'NOOP':
                    client_sock.sendall(b"250 2.0.0 OK\r\n")
                    continue
                
                # RSET reseta a transação de correio atual, mas mantém a sessão (estado GREETED)
                if cmd == 'RSET':
                    mail_from = None
                    rcpt_to = []
                    state = 'GREETED'
                    client_sock.sendall(b"250 2.0.0 Reset state\r\n")
                    continue
                
                if cmd == 'QUIT':
                    client_sock.sendall(b"221 2.0.0 localhost Service closing transmission channel\r\n")
                    client_sock.close()
                    return
                
                if cmd in ('HELO', 'EHLO'):
                    if not args:
                        client_sock.sendall(b"501 5.5.4 Syntax: HELO hostname\r\n")
                        continue
                    state = 'GREETED'
                    mail_from = None
                    rcpt_to = []
                    client_sock.sendall(f"250 Hello {args}\r\n".encode())
                    
                elif cmd == 'MAIL':
                    if state == 'INIT':
                        client_sock.sendall(b"503 5.5.3 Bad sequence of commands (HELO first)\r\n")
                        continue
                    # Parsing estrito de MAIL FROM:<email>
                    match = re.match(r'^FROM:\s*<([^>]*)>$', args, re.IGNORECASE)
                    if not match:
                        client_sock.sendall(b"501 5.5.2 Syntax error in parameters or arguments\r\n")
                        continue
                    mail_from = match.group(1)
                    state = 'MAIL'
                    rcpt_to = []
                    client_sock.sendall(b"250 2.1.0 Sender ok\r\n")
                    
                elif cmd == 'RCPT':
                    if state not in ('MAIL', 'RCPT'):
                        client_sock.sendall(b"503 5.5.3 Bad sequence of commands (MAIL FROM required)\r\n")
                        continue
                    match = re.match(r'^TO:\s*<([^>]*)>$', args, re.IGNORECASE)
                    if not match:
                        client_sock.sendall(b"501 5.5.2 Syntax error in parameters or arguments\r\n")
                        continue
                    recipient = match.group(1)
                    rcpt_to.append(recipient)
                    state = 'RCPT'
                    client_sock.sendall(b"250 2.1.5 Recipient ok\r\n")
                    
                elif cmd == 'DATA':
                    if state != 'RCPT':
                        client_sock.sendall(b"503 5.5.3 Bad sequence of commands (RCPT TO required)\r\n")
                        continue
                    
                    client_sock.sendall(b"354 Start mail input; end with <CRLF>.<CRLF>\r\n")
                    
                    # Coleta o corpo da mensagem até encontrar \r\n.\r\n
                    body_buffer = b""
                    while True:
                        chunk = client_sock.recv(1024)
                        if not chunk:
                            break
                        body_buffer += chunk
                        if b"\r\n.\r\n" in body_buffer or body_buffer.endswith(b"\n.\n"):
                            break
                    
                    # Trunca no separador de fim de dados
                    if b"\r\n.\r\n" in body_buffer:
                        message_data, _ = body_buffer.split(b"\r\n.\r\n", 1)
                    else:
                        message_data, _ = body_buffer.split(b"\n.\n", 1)
                    
                    # Dot-unstuffing (RFC 5321 Seção 4.5.2): linhas que começam com ponto duplo são reduzidas a um único ponto
                    unstopped_lines = []
                    for line_bytes in message_data.split(b"\n"):
                        clean_line = line_bytes.rstrip(b"\r")
                        if clean_line.startswith(b".."):
                            clean_line = clean_line[1:]
                        unstopped_lines.append(clean_line)
                    final_message = b"\n".join(unstopped_lines)
                    
                    print(f"[SERVIDOR] Mensagem recebida de <{mail_from}> para {rcpt_to}. Tamanho final: {len(final_message)} bytes")
                    
                    # Reset para nova transação na mesma sessão (conforme RFC 5321)
                    state = 'GREETED'
                    mail_from = None
                    rcpt_to = []
                    client_sock.sendall(b"250 2.0.0 Message accepted for delivery\r\n")
                    
                else:
                    client_sock.sendall(b"500 5.5.2 Command not recognized\r\n")


# Cliente de Teste Abrangente Validando Casos e Contraexemplos
if __name__ == '__main__':
    server = SMTPServer()
    server.start()
    print(f"[TESTE] Servidor SMTP iniciado na porta {server.port}")
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', server.port))
        
        # 1. Recepção de Boas-vindas
        resp = s.recv(1024)
        print(f"<- {resp.decode().strip()}")
        assert resp.startswith(b"220")
        
        # 2. Testar violação de ordem: MAIL antes de HELO (Deve retornar 503)
        s.sendall(b"MAIL FROM:<alice@example.com>\r\n")
        resp = s.recv(1024)
        print(f"<- {resp.decode().strip()}")
        assert resp.startswith(b"503")
        
        # 3. Testar comando desconhecido (Deve retornar 500)
        s.sendall(b"INVALIDCOMMAND\r\n")
        resp = s.recv(1024)
        print(f"<- {resp.decode().strip()}")
        assert resp.startswith(b"500")
        
        # 4. Testar comando NOOP e HELO correto
        s.sendall(b"NOOP\r\n")
        resp = s.recv(1024)
        print(f"<- {resp.decode().strip()}")
        assert resp.startswith(b"250")
        
        s.sendall(b"HELO client.local\r\n")
        resp = s.recv(1024)
        print(f"<- {resp.decode().strip()}")
        assert resp.startswith(b"250")
        
        # 5. Testar sintaxe inválida de MAIL FROM (sem angle brackets)
        s.sendall(b"MAIL FROM:alice@example.com\r\n")
        resp = s.recv(1024)
        print(f"<- {resp.decode().strip()}")
        assert resp.startswith(b"501")
        
        # 6. MAIL FROM válido
        s.sendall(b"MAIL FROM:<alice@example.com>\r\n")
        resp = s.recv(1024)
        print(f"<- {resp.decode().strip()}")
        assert resp.startswith(b"250")
        
        # 7. Testar RCPT antes de MAIL FROM em nova transação / RSET teste
        s.sendall(b"RSET\r\n")
        resp = s.recv(1024)
        print(f"<- {resp.decode().strip()}")
        assert resp.startswith(b"250")
        
        s.sendall(b"RCPT TO:<bob@example.com>\r\n")
        resp = s.recv(1024)
        print(f"<- {resp.decode().strip()}")
        assert resp.startswith(b"503") # Deve recusar pois RSET limpou o MAIL FROM
        
        # 8. Refazer MAIL FROM e testar Múltiplos Destinatários
        s.sendall(b"MAIL FROM:<alice@example.com>\r\n")
        s.recv(1024) # Consumir 250
        
        s.sendall(b"RCPT TO:<bob@example.com>\r\n")
        resp = s.recv(1024)
        print(f"<- {resp.decode().strip()}")
        assert resp.startswith(b"250")
        
        s.sendall(b"RCPT TO:<charlie@example.com>\r\n")
        resp = s.recv(1024)
        print(f"<- {resp.decode().strip()}")
        assert resp.startswith(b"250")
        
        # 9. Testar DATA e Dot-Stuffing (mensagem com linha iniciando com ponto)
        s.sendall(b"DATA\r\n")
        resp = s.recv(1024)
        print(f"<- {resp.decode().strip()}")
        assert resp.startswith(b"354")
        
        # Mensagem contendo cabeçalhos RFC 5322 e dot-stuffing (..original dot line)
        email_content = (
            b"Subject: Test RFC 5322 Message\r\n"
            b"From: alice@example.com\r\n"
            b"To: bob@example.com, charlie@example.com\r\n"
            b"\r\n"
            b"Hello Bob and Charlie,\r\n"
            b"..This line started with a dot in transmission.\r\n"
            b"End of message body.\r\n"
            b".\r\n"
        )
        s.sendall(email_content)
        resp = s.recv(1024)
        print(f"<- {resp.decode().strip()}")
        assert resp.startswith(b"250")
        
        # 10. QUIT final
        s.sendall(b"QUIT\r\n")
        resp = s.recv(1024)
        print(f"<- {resp.decode().strip()}")
        assert resp.startswith(b"221")
        
        s.close()
        print("[TESTE] Todos os testes avançados da RFC 5321 passaram com sucesso!")
        
    finally:
        server.stop()