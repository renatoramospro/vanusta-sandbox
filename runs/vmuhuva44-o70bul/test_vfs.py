import threading
import pytest
from vfs import VirtualFileSystem, FileNotFound, FileExists, IsADirectory, NotADirectory, FileSystemError

def test_basic_operations():
    vfs = VirtualFileSystem()
    vfs.create_file("/hello.txt")
    vfs.write_file("/hello.txt", b"Hello, World!")
    assert vfs.read_file("/hello.txt") == b"Hello, World!"

def test_directories_and_paths():
    vfs = VirtualFileSystem()
    vfs.mkdir("/a")
    vfs.mkdir("/a/b")
    vfs.create_file("/a/b/deep.txt")
    vfs.write_file("/a/b/deep.txt", b"deep data")
    assert vfs.read_file("/a/b/deep.txt") == b"deep data"

def test_concurrent_writes_and_integrity():
    vfs = VirtualFileSystem()
    vfs.create_file("/shared.txt")
    
    num_threads = 10
    writes_per_thread = 20
    msg_size = 12  # Tamanho fixo exato para cada mensagem formatada
    
    def worker(thread_id):
        for i in range(writes_per_thread):
            # Mensagem com formato de tamanho estrito preenchido com espaços
            raw_msg = f"T{thread_id:02d}-W{i:02d}\n"
            msg = raw_msg.encode('utf-8').ljust(msg_size, b' ')
            offset = (thread_id * writes_per_thread + i) * msg_size
            vfs.write_file("/shared.txt", msg, offset=offset)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    content = vfs.read_file("/shared.txt")
    expected_total_len = num_threads * writes_per_thread * msg_size
    assert len(content) == expected_total_len
    # Valida integridade bit a bit de cada bloco escrito
    for thread_id in range(num_threads):
        for i in range(writes_per_thread):
            raw_msg = f"T{thread_id:02d}-W{i:02d}\n"
            expected_msg = raw_msg.encode('utf-8').ljust(msg_size, b' ')
            offset = (thread_id * writes_per_thread + i) * msg_size
            chunk = content[offset:offset + msg_size]
            assert chunk == expected_msg

def test_exceptions_coverage():
    vfs = VirtualFileSystem()
    with pytest.raises(FileNotFound):
        vfs.read_file("/nonexistent")
    
    vfs.mkdir("/folder")
    with pytest.raises(IsADirectory):
        vfs.read_file("/folder")
    
    with pytest.raises(FileExists):
        vfs.mkdir("/folder")
        
    vfs.create_file("/file.txt")
    # Tentar tratar um arquivo regular como diretório deve lançar NotADirectory
    with pytest.raises(NotADirectory):
        vfs.create_file("/file.txt/sub.txt")
        
    vfs.create_file("/folder/sub.txt")
    with pytest.raises(FileSystemError):
        vfs.delete("/folder") # Diretório não vazio

def test_cwd_and_relative_paths():
    vfs = VirtualFileSystem()
    vfs.mkdir("/a")
    vfs.mkdir("/a/b")
    vfs.mkdir("/a/d")
    vfs.create_file("/a/d/file.txt")
    vfs.write_file("/a/d/file.txt", b"relative ok")
    
    vfs.chdir("/a/b")
    # Caminho relativo usando ../d/file.txt a partir de /a/b resolve para /a/d/file.txt
    content = vfs.read_file("../d/file.txt")
    assert content == b"relative ok"

def test_path_traversal_jail():
    vfs = VirtualFileSystem()
    # Tentar escapar da raiz usando múltiplos '..' deve manter o cwd/resolução na raiz
    vfs.chdir("/../../../../")
    vfs.create_file("/root_file.txt")
    assert vfs.read_file("/root_file.txt") == b""