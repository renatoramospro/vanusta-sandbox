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
                
                # O protocolo RESP envia Arrays para comandos (ex: *3\r\n$3\r\nSET\r\n...)
                if line.startswith(b'*'):
                    num_elements = int(line[1:].strip())
                    elements = []
                    for _ in range(num_elements):
                        len_line = await reader.readline()
                        if not len_line.startswith(b'$'):
                            break
                        str_len = int(len_line[1:].strip())
                        if str_len == -1:
                            elements.append(None)
                            await reader.readline() # consome o CRLF do bulk null
                        else:
                            data = await reader.readexactly(str_len)
                            await reader.readline() # consome o CRLF final do bulk string
                            elements.append(data.decode('utf-8'))
                    
                    response = self.execute_command(elements)
                    writer.write(response)
                    await writer.drain()
                else:
                    # Compatibilidade simples com comandos inline (ex: PING\r\n)
                    parts = line.strip().decode('utf-8').split()
                    if not parts:
                        continue
                    response = self.execute_command(parts)
                    writer.write(response)
                    await writer.drain()
        except asyncio.IncompleteReadError:
            pass
        finally:
            writer.close()
            await writer.wait_closed()

    def execute_command(self, args):
        if not args:
            return b"-ERR empty command\r\n"
        
        cmd = args[0].upper()
        
        if cmd == 'PING':
            return b"+PONG\r\n"
        
        elif cmd == 'SET':
            if len(args) < 3:
                return b"-ERR wrong number of arguments for 'set'\r\n"
            key, value = args[1], args[2]
            self.store[key] = value
            return b"+OK\r\n"
        
        elif cmd == 'GET':
            if len(args) < 2:
                return b"-ERR wrong number of arguments for 'get'\r\n"
            key = args[1]
            if key in self.store:
                val = self.store[key]
                return f"${len(val)}\r\n{val}\r\n".encode('utf-8')
            else:
                return b"$-1\r\n" # Null bulk string para chave inexistente
        
        elif cmd == 'DEL':
            if len(args) < 2:
                return b"-ERR wrong number of arguments for 'del'\r\n"
            key = args[1]
            deleted = 1 if self.store.pop(key, None) is not None else 0
            return f":{deleted}\r\n".encode('utf-8')
        
        else:
            return f"-ERR unknown command '{cmd}'\r\n".encode('utf-8')

async def start_server(host='127.0.0.1', port=0):
    server_obj = RESPServer()
    server = await asyncio.start_server(server_obj.handle_client, host, port)
    addr = server.sockets[0].getsockname()
    return server, addr[1]