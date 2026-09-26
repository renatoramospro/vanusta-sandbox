import asyncio
import pytest
from resp_server import run_server

@pytest.mark.asyncio
async def test_resp_server_operations():
    srv, port = await run_server()
    reader, writer = await asyncio.open_connection('127.0.0.1', port)

    # 1. PING
    writer.write(b"*1\r\n$4\r\nPING\r\n")
    await writer.drain()
    assert await reader.readline() == b"+PONG\r\n"

    # 2. SET
    writer.write(b"*3\r\n$3\r\nSET\r\n$3\r\nfoo\r\n$3\r\nbar\r\n")
    await writer.drain()
    assert await reader.readline() == b"+OK\r\n"

    # 3. GET
    writer.write(b"*2\r\n$3\r\nGET\r\n$3\r\nfoo\r\n")
    await writer.drain()
    assert await reader.readline() == b"$3\r\n"
    assert await reader.readline() == b"bar\r\n"

    # 4. GET Miss (Bulk String nula) - Corrigido tamanho para 11 bytes ("nonexistent")
    writer.write(b"*2\r\n$3\r\nGET\r\n$11\r\nnonexistent\r\n")
    await writer.drain()
    assert await reader.readline() == b"$-1\r\n"

    # 5. DEL
    writer.write(b"*2\r\n$3\r\nDEL\r\n$3\r\nfoo\r\n")
    await writer.drain()
    assert await reader.readline() == b":1\r\n"

    writer.close()
    await writer.wait_closed()
    srv.close()
    await srv.wait_closed()

@pytest.mark.asyncio
async def test_malformed_command():
    srv, port = await run_server()
    reader, writer = await asyncio.open_connection('127.0.0.1', port)

    writer.write(b"*2\r\n$3\r\nSET\r\nINVALID\r\n")
    await writer.drain()
    resp = await reader.readline()
    assert resp == b"-ERR malformed command\r\n"

    # Confirma que o servidor continua funcional após rejeitar o malformado
    writer.write(b"*1\r\n$4\r\nPING\r\n")
    await writer.drain()
    assert await reader.readline() == b"+PONG\r\n"

    writer.close()
    await writer.wait_closed()
    srv.close()
    await srv.wait_closed()

@pytest.mark.asyncio
async def test_pipelining():
    srv, port = await run_server()
    reader, writer = await asyncio.open_connection('127.0.0.1', port)

    pipeline_data = (
        b"*1\r\n$4\r\nPING\r\n"
        b"*3\r\n$3\r\nSET\r\n$4\r\npipe\r\n$5\r\nvalue\r\n"
        b"*2\r\n$3\r\nGET\r\n$4\r\npipe\r\n"
    )
    writer.write(pipeline_data)
    await writer.drain()

    assert await reader.readline() == b"+PONG\r\n"
    assert await reader.readline() == b"+OK\r\n"
    assert await reader.readline() == b"$5\r\n"
    assert await reader.readline() == b"value\r\n"

    writer.close()
    await writer.wait_closed()
    srv.close()
    await srv.wait_closed()

@pytest.mark.asyncio
async def test_concurrent_clients():
    srv, port = await run_server()

    async def client_task(i):
        reader, writer = await asyncio.open_connection('127.0.0.1', port)
        key = f"key_{i}".encode()
        val = f"val_{i}".encode()

        # SET
        writer.write(b"*3\r\n$3\r\nSET\r\n$" + str(len(key)).encode() + b"\r\n" + key + b"\r\n$" + str(len(val)).encode() + b"\r\n" + val + b"\r\n")
        await writer.drain()
        assert await reader.readline() == b"+OK\r\n"

        # GET
        writer.write(b"*2\r\n$3\r\nGET\r\n$" + str(len(key)).encode() + b"\r\n" + key + b"\r\n")
        await writer.drain()
        l1 = await reader.readline()
        l2 = await reader.readline()
        assert l1 == f"${len(val)}\r\n".encode()
        assert l2 == val + b"\r\n"

        writer.close()
        await writer.wait_closed()

    await asyncio.gather(*(client_task(i) for i in range(50)))

    srv.close()
    await srv.wait_closed()