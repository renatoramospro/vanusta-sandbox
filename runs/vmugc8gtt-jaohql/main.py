import ssl
import socket

# Criação de uma CA Raiz
ca_root = ssl.DER_cert_to_pem_cert(open('ca_root.crt', 'rb').read())

# Geração de CSR para o servidor
server_csr = ssl.DER_cert_to_pem_cert(open('server_csr.pem', 'rb').read())

# Assinatura do CSR pelo servidor
server_cert = ssl.DER_cert_to_pem_cert(open('server_cert.pem', 'rb').read())

# Criação de um cliente
client_cert = ssl.DER_cert_to_pem_cert(open('client_cert.pem', 'rb').read())
client_key = open('client_key.pem', 'rb').read()

# Configuração do servidor
server_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
server_context.load_cert_chain(server_cert, ca_certs=ca_root, ca_cert_dir=None)

# Configuração do cliente
client_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
client_context.load_cert_chain(client_cert, keyfile=client_key)

# Estabelecimento da conexão
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('localhost', 8080))
server_socket.listen(1)

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('localhost', 8080))

# Comunicação segura
server_socket = server_context.wrap_socket(server_socket, server_side=True)
client_socket = client_context.wrap_socket(client_socket, server_hostname='localhost')

# Envio de dados
server_socket.sendall(b'Hello, world!')
client_socket.sendall(b'Hello, server!')

# Recepção de dados
data = client_socket.recv(1024)
print(data.decode())

# Fechamento da conexão
server_socket.close()
client_socket.close()