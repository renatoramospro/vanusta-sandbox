import socket
import struct
import binascii

# Constantes
OP_CONTINUATION = 0x0
OP_TEXT = 0x1
OP_BINARY = 0x2
OP_CLOSE = 0x8
OP_PING = 0x9
OP_PONG = 0xA

# Função para criar um socket TCP
def criar_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    return sock

# Função para estabelecer uma conexão com um cliente web padrão
def estabelecer_conexao(sock, endereco):
    sock.connect(endereco)

# Função para realizar o handshake HTTP
def realizar_handshake(sock):
    # Enviar requisição HTTP inicial
    requisicao = "GET / HTTP/1.1\r\nHost: localhost\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Version: 13\r\nSec-WebSocket-Key: 1234567890abcdef\r\n\r\n"
    sock.sendall(requisicao.encode())

    # Receber resposta HTTP
    resposta = sock.recv(1024)
    print(resposta.decode())

# Função para enviar um frame de dados
def enviar_frame(sock, opcode, dados):
    # Criar cabeçalho do frame
    cabecalho = struct.pack("!B", opcode)
    cabecalho += struct.pack("!H", len(dados))

    # Enviar frame
    sock.sendall(cabecalho + dados)

# Função para receber um frame de dados
def receber_frame(sock):
    # Receber cabeçalho do frame
    cabecalho = sock.recv(2)
    opcode = struct.unpack("!B", cabecalho)[0]
    tamanho = struct.unpack("!H", cabecalho[1:3])[0]

    # Receber dados do frame
    dados = sock.recv(tamanho)

    return opcode, dados

# Função para parsear um frame de dados
def parsear_frame(opcode, dados):
    if opcode == OP_TEXT:
        # Extrair texto do frame
        texto = dados.decode()
        return texto
    elif opcode == OP_BINARY:
        # Extrair dados binários do frame
        dados_binarios = dados
        return dados_binarios
    else:
        return None

# Função para enviar uma mensagem de volta ao cliente web padrão
def enviar_mensagem(sock, mensagem):
    # Criar frame de dados
    frame = struct.pack("!B", OP_TEXT) + struct.pack("!H", len(mensagem)) + mensagem.encode()

    # Enviar frame
    sock.sendall(frame)

# Função principal
def main():
    # Criar socket TCP
    sock = criar_socket()

    # Estabelecer conexão com um cliente web padrão
    endereco = ("localhost", 8080)
    estabelecer_conexao(sock, endereco)

    # Realizar handshake HTTP
    realizar_handshake(sock)

    # Enviar um frame de dados
    opcode = OP_TEXT
    dados = "Olá, mundo!"
    enviar_frame(sock, opcode, dados)

    # Receber um frame de dados
    opcode, dados = receber_frame(sock)
    print("Recebido:", opcode, dados.decode())

    # Parsear frame de dados
    texto = parsear_frame(opcode, dados)
    print("Texto:", texto)

    # Enviar uma mensagem de volta ao cliente web padrão
    mensagem = "Olá novamente, mundo!"
    enviar_mensagem(sock, mensagem)

    # Fechar conexão
    sock.close()

if __name__ == "__main__":
    main()