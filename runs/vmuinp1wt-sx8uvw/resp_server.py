import asyncio

class RESPServer:
    def __init__(self):
        self.store = {}

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            while True:
                try:
                    line = await reader.readline()
                except (asyncio.IncompleteReadError, ConnectionResetError):
                    break

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
                        try:
                            len_line = await reader.readline()
                        except (asyncio.IncompleteReadError, ConnectionResetError):
                            malformed = True
                            break

                        if not len_line or not len_line.startswith(b'$'):
                            malformed = True
                            break
                        try:
                            str_len = int(len_line[1:].strip())
                        except ValueError:
                            malformed = True
                            break

                        if str_len == -1:
                            elements.append(None)
                        else:
                            try:
                                data = await reader.readexactly(str_len)
                                crlf = await reader.readexactly(2)
                                if crlf != b'\r\n':
                                    malformed = True
                                    break
                            except (asyncio.IncompleteReadError, ConnectionResetError):
                                malformed = True
                                break
                            elements.append(data)

                    if malformed:
                        writer.write(b"-ERR malformed command\r\n")
                        await writer.drain()
                        continue

                    if not elements:
                        writer.write(b"-ERR empty command\r\n")
                        await writer.drain()
                        continue

                    cmd = elements[0].upper()
                    if cmd == b'PING':
                        writer.write(b"+PONG\r\n")
                        await writer.drain()
                    elif cmd == b'SET':
                        if len(elements) != 3:
                            writer.write(b"-ERR wrong number of arguments for SET\r\n")
                        else:
                            self.store[elements[1]] = elements[2]
                            writer.write(b"+OK\r\n")
                        await writer.drain()
                    elif cmd == b'GET':
                        if len(elements) != 2:
                            writer.write(b"-ERR wrong number of arguments for GET\r\n")
                        else:
                            val = self.store.get(elements[1])
                            if val is None:
                                writer.write(b"$-1\r\n")
                            else:
                                writer.write(f"${len(val)}\r\n".encode() + val + b"\r\n")
                        await writer.drain()
                    elif cmd == b'DEL':
                        if len(elements) < 2:
                            writer.write(b"-ERR wrong number of arguments for DEL\r\n")
                        else:
                            deleted_count = 0
                            for k in elements[1:]:
                                if k in self.store:
                                    del self.store[k]
                                    deleted_count += 1
                            writer.write(f":{deleted_count}\r\n".encode())
                        await writer.drain()
                    else:
                        writer.write(f"-ERR unknown command '{cmd.decode(errors='ignore')}'\r\n".encode())
                        await writer.drain()
                else:
                    writer.write(b"-ERR protocol error\r\n")
                    await writer.drain()
        except Exception:
            pass
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

async def run_server():
    server_instance = RESPServer()
    server = await asyncio.start_server(server_instance.handle_client, '127.0.0.1', 0)
    addr = server.sockets[0].getsockname()
    return server, addr[1]