import asyncio
import pytest
from resp_server import start_server

@pytest.mark.asyncio
async def test_resp_commands():
    server, port = await start_server()
    
    # Conecta um cliente TCP simulado
    reader, writer = await asyncio.open_connection('127.0.0.1', port)
    
    # 1. Testando PING (Comando Inline)
    writer.write(b"PING\r\n")
    await writer.drain()
    response = await reader.readline()
    assert response == b"+PONG\r\n"
    print(f"Sucesso PING: {response}")

    # 2. Testando SET (Formato Array RESP)
    # *3\r\n$3\r\nSET\r\n$3\r\nfoo\r\n$3\r\nbar\r\n
    cmd_set = b"*3\r\n$3\r\nSET\r\n$3\r\nfoo\r\n$3\r\nbar\r\n"
    writer.write(cmd_set)
    await writer.drain()
    response = await reader.readline()
    assert response == b"+OK\r\n"
    print(f"Sucesso SET: {response}")

    # 3. Testando GET (Formato Array RESP)
    # *2\r\n$3\r\nGET\r\n$3\r\nfoo\r\n
    cmd_get = b"*2\r\n$3\r\nGET\r\n$3\r\nfoo\r\n"
    writer.write(cmd_get)
    await writer.drain()
    line1 = await reader.readline() # $3
    line2 = await reader.readline() # bar\r\n
    assert line1 == b"$3\r\n"
    assert line2 == b"bar\r\n"
    print(f"Sucesso GET: {line1}{line2}")

    # 4. Testando GET com chave inexistente (Null Bulk String)
    cmd_get_miss = b"*2\r\n$3\r\nGET\r\n$9\r\nnotexist\r\n"
    writer.write(cmd_get_miss)
    await writer.drain()
    response = await reader.readline()
    assert response == b"$-1\r\n"
    print(f"Sucesso GET Miss: {response}")

    # 5. Testando DEL (Deleção de chave)
    cmd_del = b"*2\r\n$3\r\nDEL\r\n$3\r\nfoo\r\n"
    writer.write(cmd_del)
    await writer.drain()
    response = await reader.readline()
    assert response == b":1\r\n"
    print(f"Sucesso DEL: {response}")

    # Contraexemplo / Tratamento de equívoco comum: Parsing ingênuo por split por espaço
    # Se tratarmos payloads que contêm espaços ou quebras de linha usando apenas .split() 
    # em cima de uma linha inteira sem respeitar o protocolo de Bulk Strings do RESP, 
    # valores com espaços quebrariam o parser. O RESP resolve isso explicitamente com o tamanho do Bulk String ($len).
    # Vamos demonstrar que nosso parser lida corretamente com dados contendo espaços:
    cmd_set_space = b"*3\r\n$3\r\nSET\r\n$3\r\nkey\r\n$11\r\nhello world\r\n"
    writer.write(cmd_set_space)
    await writer.drain()
    resp_ok = await reader.readline()
    assert resp_ok == b"+OK\r\n"

    cmd_get_space = b"*2\r\n$3\r\nGET\r\n$3\r\nkey\r\n"
    writer.write(cmd_get_space)
    await writer.drain()
    l1 = await reader.readline() # $11
    l2 = await reader.readline() # hello world\r\n
    assert l1 == b"$11\r\n"
    assert l2 == b"hello world\r\n"
    print(f"Sucesso Bulk String com espaços: {l1}{l2}")

    writer.close()
    await writer.wait_closed()
    server.close()
    await server.wait_closed()