import asyncio

MAX_ELEMENTS = 1024
MAX_BULK_LEN = 512 * 1024 * 1024  # 512 MB
READ_TIMEOUT = 5.0  # segundos

class RESPServer:
    def __init__(self):
        self.store = {}

    async def _safe_readline(self, reader: asyncio.StreamReader) -> bytes:
        line = await asyncio.wait_for(reader.readline(), timeout=READ_TIMEOUT)
        if not line.endswith(b'\r\n'):
            raise ValueError("strict CRLF required")
        return line

    async def _safe_readexactly(self, reader: asyncio.StreamReader, n: int) -> bytes:
        return await asyncio.wait_for(reader.readexactly(n), timeout=READ_TIMEOUT)

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            while True:
                try:
                    line = await self._safe_readline(reader)
                except (asyncio.IncompleteReadError, ConnectionResetError, asyncio.TimeoutError, ValueError):
                    break

                if not line:
                    break
                
                if line.startswith(b'*'):
                    try:
                        num_elements = int(line[1:-2].strip())
                    except ValueError:
                        writer.write(b"-ERR invalid array length\r\n")
                        await writer.drain()
                        continue

                    if num_elements < 0 or num_elements > MAX_ELEMENTS:
                        writer.write(b"-ERR array length out of range\r\n")
                        await writer.drain()
                        continue

                    elements = []
                    malformed = False
                    for _ in range(num_elements):
                        try:
                            len_line = await self._safe_readline(reader)
                        except (asyncio.IncompleteReadError, ConnectionResetError, asyncio.TimeoutError, ValueError):
                            malformed = True
                            break

                        if not len_line or not len_line.startswith(b'$'):
                            malformed = True
                            break
                        try:
                            str_len = int(len_line[1:-2].strip())
                        except ValueError:
                            malformed = True
                            break

                        if str_len == -1:
                            elements.append(None)
                        elif str_len < -1 or str_len > MAX_BULK_LEN:
                            malformed = True
                            break
                        else:
                            try:
                                data = await self._safe_readexactly(reader, str_len)
                                crlf = await self._safe_readexactly(reader, 2)
                                if crlf != b'\r\n':
                                    malformed = True
                                    break
                                elements.append(data)
                            except (asyncio.IncompleteReadError, ConnectionResetError, asyncio.TimeoutError):
                                malformed = True
                                break

                    if malformed:
                        writer.write(b"-ERR malformed command\r\n")
                        await writer.drain()
                        break

                    if not elements:
                        writer.write(b"-ERR empty command\r\n")
                        await writer.drain()
                        continue

                    cmd = elements[0].upper()
                    if cmd == b'PING':
                        if len(elements) > 1 and elements[1] is not None:
                            val = elements[1]
                            writer.write(f"${len(val)}\r\n".encode() + val + b"\r\n")
                        else:
                            writer.write(b"+PONG\r\n")
                        await writer.drain()

                    elif cmd == b'SET':
                        if len(elements) < 3 or elements[1] is None or elements[2] is None:
                            writer.write(b"-ERR wrong number of arguments for SET\r\n")
                        else:
                            self.store[elements[1]] = elements[2]
                            writer.write(b"+OK\r\n")
                        await writer.drain()

                    elif cmd == b'GET':
                        if len(elements) < 2 or elements[1] is None:
                            writer.write(b"-ERR wrong number of arguments for GET\r\n")
                        else:
                            val = self.store.get(elements[1])
                            if val is None:
                                writer.write(b"$-1\r\n")
                            else:
                                writer.write(f"${len(val)}\r\n".encode() + val + b"\r\n")
                        await writer.drain()

                    elif cmd == b'DEL':
                        if len(elements) < 2 or elements[1] is None:
                            writer.write(b"-ERR wrong number of arguments for DEL\r\n")
                        else:
                            key = elements[1]
                            deleted = 1 if key in self.store else 0
                            if deleted:
                                del self.store[key]
                            writer.write(f":{deleted}\r\n".encode())
                        await writer.drain()
                    else:
                        writer.write(b"-ERR unknown command\r\n")
                        await writer.drain()
                else:
                    writer.write(b"-ERR invalid command start\r\n")
                    await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

async def start_server(host='127.0.0.1', port=0):
    server = RESPServer()
    srv = await asyncio.start_server(server.handle_client, host, port)
    addr = srv.sockets[0].getsockname()
    return srv, addr[1]