import pytest
import threading
from vfs import VirtualFileSystem, FileNotFound, FileExists, IsADirectory, NotADirectory, FileSystemError

def test_basic_file_lifecycle():
    vfs = VirtualFileSystem()
    vfs.mkdir("/docs")
    vfs.create_file("/docs/note.txt")
    
    content = b"Hello, Virtual File System!"
    vfs.write_file("/docs/note.txt", content)
    
    read_data = vfs.read_file("/docs/note.txt")
    assert read_data == content
    
    vfs.delete("/docs/note.txt")
    with pytest.raises(FileNotFound):
        vfs.read_file("/docs/note.txt")

def test_nested_paths_and_navigation():
    vfs = VirtualFileSystem()
    vfs.mkdir("/a")
    vfs.mkdir("/a/b")
    vfs.mkdir("/a/b/c")
    vfs.create_file("/a/b/c/deep.txt")
    
    vfs.write_file("/a/b/c/deep.txt", b"deep data")
    assert vfs.read_file("/a/b/c/deep.txt") == b"deep data"
    
    # Testando navegação com diretórios correntes virtuais /..
    assert vfs.read_file("/a/../a/b/c/../c/deep.txt") == b"deep data"

def test_concurrent_writes_and_integrity():
    vfs = VirtualFileSystem()
    vfs.create_file("/shared.txt")
    
    num_threads = 10
    writes_per_thread = 20
    
    def worker(thread_id):
        for i in range(writes_per_thread):
            msg = f"T{thread_id}-W{i}\n".encode()
            # Cada thread escreve em um offset seguro exclusivo para validar integridade sem sobrescrita destrutiva cega
            offset = (thread_id * writes_per_thread + i) * len(msg)
            vfs.write_file("/shared.txt", msg, offset=offset)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    content = vfs.read_file("/shared.txt")
    assert len(content) == num_threads * writes_per_thread * len(b"T0-W0\n")

def test_exceptions_coverage():
    vfs = VirtualFileSystem()
    with pytest.raises(FileNotFound):
        vfs.read_file("/nonexistent")
    
    vfs.mkdir("/folder")
    with pytest.raises(IsADirectory):
        vfs.read_file("/folder")
    
    with pytest.raises(FileExists):
        vfs.mkdir("/folder")
        
    with pytest.raises(NotADirectory):
        vfs.create_file("/folder/file.txt")
        
    with pytest.raises(FileSystemError):
        vfs.delete("/folder") # Diretório não vazio (contém . e .. mas sem filhos extras, falha se tentar deletar raiz ou com filhos)
        
    vfs.create_file("/folder/sub.txt")
    with pytest.raises(FileSystemError):
        vfs.delete("/folder")