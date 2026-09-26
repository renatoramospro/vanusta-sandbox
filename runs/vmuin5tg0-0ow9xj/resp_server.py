import asyncio

class RESPServer:
    def __init__(self):
        self.store = {}

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            while True:
                line = await reader.readline()
                if not line:
                    break
                
                if line.startswith(b'*'):
                    try:
                        num_elements = int(line[1:].strip())
                    except ValueError:
                        writer.write(b"-ERR invalid array length\r\n")
                        await writer.drain()
                        continue

                    elements = []
                    malformed = False
                    for _ in range(num_elements):
                        len_line = await reader.readline()
                        if not len_line.startswith(b'$'):
                            malformed = True
                            break
                        try:
                            str_len = int(len_line[1:].strip())
                        except ValueError:
                            malformed = True
                            break

                        if str_len == -1:
                            elements.append(None)
                            # $-1\r\n NÃO possui payload e nem CRLF adicional de dados.
                        else:
                            data = await reader.readexactly(str_len)
                            crlf = await reader.readexactly(2)
                            if crlf != b'\r\n':
                                malformed = True
                                break
                            elements.append(data)

                    if malformed:
                        writer.write(b"-ERR malformed command\r\n")
                        await writer.drain()
                        continue

                    response = await self.execute_command(elements)
                    writer.write(response)
                    await writer.drain()
                else:
                    writer.write(b"-ERR unknown protocol\r\n")
                    await writer.drain()
        except asyncio.IncompleteReadError:
            pass
        except ConnectionResetError:
            pass
        finally:
            writer.close()
            await writer.wait_closed()

    async def execute_command(self, elements):
        if not elements:
            return b"-ERR empty command\r\n"
        
        cmd = elements[0].upper()

        if cmd == b'PING':
            return b"+PONG\r\n"
        
        elif cmd == b'SET' and len(elements) == 3:
            key = elements[1]
            value = elements[2]
            self.store[key] = value
            return b"+OK\r\n"
        
        elif cmd == b'GET' and len(elements) == 2:
            key = elements[1]
            val = self.store.get(key)
            if val is None:
                return b"$-1\r\n"
            return f"${len(val)}\r\n".encode() + val + b"\r\n"
        
        elif cmd == b'DEL' and len(elements) == 2:
            key = elements[1]
            existed = 1 if key in self.store else 0
            if existed:
                del self.store[key]
            return f":{existed}\r\n".encode()
        
        return b"-ERR unsupported command or wrong arguments\r\n"

async def run_server():
    server = RESPServer()
    srv = await asyncio.start_server(server.handle_client, '127.0.0.1', 0)
    addr = srv.sockets[0].getsockname()
    return srv, addr[1]