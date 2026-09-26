import threading
import time
import os
from typing import Dict, List, Optional, Union

class FileSystemError(Exception):
    pass

class FileNotFound(FileSystemError):
    pass

class FileExists(FileSystemError):
    pass

class IsADirectory(FileSystemError):
    pass

class NotADirectory(FileSystemError):
    pass

class PermissionDenied(FileSystemError):
    pass

class Inode:
    def __init__(self, ino: int, is_dir: bool, permissions: int = 0o755):
        self.ino = ino
        self.is_dir = is_dir
        self.size = 0
        self.permissions = permissions
        self.uid = 0
        self.gid = 0
        self.created_at = time.time()
        self.modified_at = self.created_at
        self.accessed_at = self.created_at
        self.nlink = 1
        self.data = bytearray() if not is_dir else None
        self.entries: Dict[str, int] = {} if is_dir else None  # Nome -> Ino
        self.lock = threading.RLock()

class VirtualFileSystem:
    def __init__(self):
        self.lock = threading.RLock()
        self.inodes: Dict[int, Inode] = {}
        self.next_ino = 1
        
        # Criação do diretório raiz
        root_inode = self._alloc_inode(is_dir=True)
        self.root_ino = root_inode.ino
        self.inodes[self.root_ino].entries['.'] = self.root_ino
        self.inodes[self.root_ino].entries['..'] = self.root_ino

    def _alloc_inode(self, is_dir: bool, permissions: int = 0o755) -> Inode:
        with self.lock:
            ino = self.next_ino
            self.next_ino += 1
            inode = Inode(ino, is_dir, permissions)
            self.inodes[ino] = inode
            return inode

    def _resolve_path(self, path: str, current_dir_ino: int) -> int:
        """Resolve um caminho absoluto ou relativo até o inode correspondente."""
        if not path:
            return current_dir_ino

        parts = [p for p in path.split('/') if p and p != '.']
        
        if path.startswith('/'):
            curr = self.root_ino
        else:
            curr = current_dir_ino

        for part in parts:
            if part == '..':
                with self.inodes[curr].lock:
                    if self.inodes[curr].entries and '..' in self.inodes[curr].entries:
                        curr = self.inodes[curr].entries['..']
            else:
                inode = self.inodes[curr]
                if not inode.is_dir:
                    raise NotADirectory(f"Não é um diretório")
                
                with inode.lock:
                    if part not in inode.entries:
                        raise FileNotFound(f"Caminho não encontrado: {part}")
                    curr = inode.entries[part]
        return curr

    def mkdir(self, path: str, current_dir_ino: int = 1) -> int:
        with self.lock:
            parent_path, name = os.path.split(path)
            if not name and parent_path:
                # Caminho termina com '/'
                parent_path, name = os.path.split(parent_path)
            
            parent_ino = self._resolve_path(parent_path if parent_path else '.', current_dir_ino)
            
            parent_node = self.inodes[parent_ino]
            with parent_node.lock:
                if name in parent_node.entries:
                    raise FileExists(f"Diretório ou arquivo já existe: {name}")
                
                new_inode = self._alloc_inode(is_dir=True)
                new_inode.entries['.'] = new_inode.ino
                new_inode.entries['..'] = parent_ino
                
                parent_node.entries[name] = new_inode.ino
                parent_node.nlink += 1
                parent_node.modified_at = time.time()
                return new_inode.ino

    def create_file(self, path: str, current_dir_ino: int = 1) -> int:
        with self.lock:
            parent_path, name = os.path.split(path)
            parent_ino = self._resolve_path(parent_path if parent_path else '.', current_dir_ino)
            
            parent_node = self.inodes[parent_ino]
            with parent_node.lock:
                if name in parent_node.entries:
                    raise FileExists(f"Arquivo já existe: {name}")
                
                new_inode = self._alloc_inode(is_dir=False)
                parent_node.entries[name] = new_inode.ino
                parent_node.modified_at = time.time()
                return new_inode.ino

    def write_file(self, path: str, data: bytes, offset: int = 0, current_dir_ino: int = 1):
        ino = self._resolve_path(path, current_dir_ino)
        inode = self.inodes[ino]
        if inode.is_dir:
            raise IsADirectory(f"É um diretório: {path}")
        
        with inode.lock:
            required_len = offset + len(data)
            if required_len > len(inode.data):
                inode.data.extend(b'\x00' * (required_len - len(inode.data)))
            inode.data[offset:offset+len(data)] = data
            inode.size = len(inode.data)
            inode.modified_at = time.time()

    def read_file(self, path: str, size: Optional[int] = None, offset: int = 0, current_dir_ino: int = 1) -> bytes:
        ino = self._resolve_path(path, current_dir_ino)
        inode = self.inodes[ino]
        if inode.is_dir:
            raise IsADirectory(f"É um diretório: {path}")
        
        with inode.lock:
            inode.accessed_at = time.time()
            data = bytes(inode.data)
            if size is None:
                return data[offset:]
            return data[offset:offset+size]

    def delete(self, path: str, current_dir_ino: int = 1):
        with self.lock:
            parent_path, name = os.path.split(path)
            if not name:
                raise FileSystemError("Operação inválida")
            
            parent_ino = self._resolve_path(parent_path if parent_path else '.', current_dir_ino)
            parent_node = self.inodes[parent_ino]
            
            with parent_node.lock:
                if name not in parent_node.entries:
                    raise FileNotFound(f"Não encontrado: {name}")
                
                ino = parent_node.entries[name]
                target_node = self.inodes[ino]
                
                with target_node.lock:
                    if target_node.is_dir and len([k for k in target_node.entries if k not in ('.', '..')]) > 0:
                        raise FileSystemError("Diretório não está vazio")
                    
                    del parent_node.entries[name]
                    if target_node.is_dir:
                        parent_node.nlink -= 1
                    
                    target_node.nlink -= 1
                    if target_node.nlink <= 0:
                        del self.inodes[ino]
                parent_node.modified_at = time.time()