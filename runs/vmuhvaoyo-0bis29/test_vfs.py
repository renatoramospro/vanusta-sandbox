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
    vfs.mkdir("/documents")
    vfs.create_file("/documents/note.txt")
    vfs.write_file("/documents/note.txt", b"VFS Content")
    assert vfs.read_file("/documents/note.txt") == b"VFS Content"

def test_concurrent_writes_and_integrity():
    vfs = VirtualFileSystem()
    vfs.create_file("/shared.dat")
    
    num_threads = 10
    writes_per_thread = 20
    msg_size = 16  # Tamanho fixo exato para evitar sobreposições e lacunas
    
    def worker(thread_id):
        for i in range(writes_per_thread):
            msg = f"T{thread_id}-W{i}".encode('utf-8').ljust(msg_size, b' ')
            offset = (thread_id * writes_per_thread + i) * msg_size
            vfs.write_file("/shared.dat", msg, offset=offset)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
        
    content = vfs.read_file("/shared.dat")
    expected_total_size = num_threads * writes_per_thread * msg_size
    assert len(content) == expected_total_size
    
    # Verificar integridade bit a bit de cada bloco exclusivo
    for thread_id in range(num_threads):
        for i in range(writes_per_thread):
            expected_msg = f"T{thread_id}-W{i}".encode('utf-8').ljust(msg_size, b' ')
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
    content = vfs.read_file("../d/file.txt")
    assert content == b"relative ok"

def test_path_traversal_jail():
    vfs = VirtualFileSystem()
    vfs.chdir("/../../../../")
    vfs.create_file("/root_file.txt")
    assert vfs.read_file("/root_file.txt") == b""