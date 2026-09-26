import threading
import pytest
from vfs import VirtualFileSystem, FileNotFound, FileExists, IsADirectory

def test_basic_file_operations():
    vfs = VirtualFileSystem()
    vfs.mkdir("/docs")
    vfs.create_file("/docs/test.txt")
    
    vfs.write_file("/docs/test.txt", b"Hello, VFS!")
    content = vfs.read_file("/docs/test.txt")
    assert content == b"Hello, VFS!"

def test_relative_paths():
    vfs = VirtualFileSystem()
    vfs.mkdir("/a")
    vfs.mkdir("/a/b")
    ino_a = vfs._resolve_path("/a", 1)
    
    vfs.create_file("file.txt", current_dir_ino=ino_a)
    assert vfs.read_file("/a/file.txt") == b""

def test_concurrent_writes():
    vfs = VirtualFileSystem()
    vfs.create_file("/shared.txt")
    
    def worker(thread_id):
        data = f"data-{thread_id}\n".encode()
        for _ in range(50):
            vfs.write_file("/shared.txt", data, offset=0)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # Verifica integridade básica pós-concorrência
    content = vfs.read_file("/shared.txt")
    assert len(content) > 0

def test_exceptions():
    vfs = VirtualFileSystem()
    with pytest.raises(FileNotFound):
        vfs.read_file("/nonexistent")
    
    vfs.mkdir("/folder")
    with pytest.raises(IsADirectory):
        vfs.read_file("/folder")
    
    with pytest.raises(FileExists):
        vfs.mkdir("/folder")