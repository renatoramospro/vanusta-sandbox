import threading
import time
from typing import Dict, List, Optional

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

    def _resolve_path(self, path: str) -> List[str]:
        if not path.startswith('/'):
            raise FileSystemError("Caminhos relativos diretos não suportados sem contexto de cwd")
        parts = [p for p in path.split('/') if p and p != '.']
        resolved = []
        for p in parts:
            if p == '..':
                if resolved:
                    resolved.pop()
            else:
                resolved.append(p)
        return resolved

    def _get_parent_and_basename(self, path: str) -> (Inode, str):
        parts = self._resolve_path(path)
        if not parts:
            raise FileSystemError("Operação inválida no diretório raiz")
        
        basename = parts[-1]
        parent_parts = parts[:-1]
        
        curr_ino = self.root_ino
        for part in parent_parts:
            curr_inode = self.inodes[curr_ino]
            with curr_inode.lock:
                if part not in curr_inode.entries:
                    raise FileNotFound(f"Diretório não encontrado: {part}")
                next_ino = curr_inode.entries[part]
                next_inode_obj = self.inodes[next_ino]
                if not next_inode_obj.is_dir:
                    raise NotADirectory(f"Não é um diretório: {part}")
                curr_ino = next_ino
        
        return self.inodes[curr_ino], basename

    def mkdir(self, path: str, permissions: int = 0o755):
        with self.lock:
            parent, name = self._get_parent_and_basename(path)
            with parent.lock:
                if name in parent.entries:
                    raise FileExists(f"Arquivo ou diretório já existe: {name}")
                
                new_dir = self._alloc_inode(is_dir=True, permissions=permissions)
                parent.entries[name] = new_dir.ino
                new_dir.entries['.'] = new_dir.ino
                new_dir.entries['..'] = parent.ino
                parent.nlink += 1
                parent.modified_at = time.time()

    def create_file(self, path: str, permissions: int = 0o644):
        with self.lock:
            parent, name = self._get_parent_and_basename(path)
            with parent.lock:
                if name in parent.entries:
                    raise FileExists(f"Arquivo já existe: {name}")
                
                new_file = self._alloc_inode(is_dir=False, permissions=permissions)
                parent.entries[name] = new_file.ino
                parent.modified_at = time.time()

    def write_file(self, path: str, data: bytes, offset: int = 0):
        inode = self._get_inode_by_path(path)
        if inode.is_dir:
            raise IsADirectory("Não é permitido escrever em um diretório")
        
        with inode.lock:
            if offset > len(inode.data):
                inode.data.extend(b'\x00' * (offset - len(inode.data)))
            
            end_pos = offset + len(data)
            if end_pos > len(inode.data):
                inode.data[offset:] = data
            else:
                inode.data[offset:end_pos] = data
            
            inode.size = len(inode.data)
            inode.modified_at = time.time()

    def read_file(self, path: str, size: Optional[int] = None, offset: int = 0) -> bytes:
        inode = self._get_inode_by_path(path)
        if inode.is_dir:
            raise IsADirectory("Não é possível ler um diretório como arquivo")
        
        with inode.lock:
            inode.accessed_at = time.time()
            if offset >= len(inode.data):
                return b''
            if size is None:
                return bytes(inode.data[offset:])
            return bytes(inode.data[offset:offset + size])

    def delete(self, path: str):
        with self.lock:
            parent, name = self._get_parent_and_basename(path)
            with parent.lock:
                if name not in parent.entries:
                    raise FileNotFound(f"Caminho não encontrado: {name}")
                
                ino = parent.entries[name]
                inode = self.inodes[ino]
                
                with inode.lock:
                    if inode.is_dir and len([k for k in inode.entries if k not in ('.', '..')]) > 0:
                        raise FileSystemError("Diretório não está vazio")
                    
                    del parent.entries[name]
                    parent.modified_at = time.time()
                    if inode.is_dir:
                        parent.nlink -= 1
                    
                    inode.nlink -= 1

    def _get_inode_by_path(self, path: str) -> Inode:
        parts = self._resolve_path(path)
        curr_ino = self.root_ino
        for part in parts:
            curr_inode = self.inodes[curr_ino]
            with curr_inode.lock:
                if part not in curr_inode.entries:
                    raise FileNotFound(f"Caminho não encontrado: {part}")
                curr_ino = curr_inode.entries[part]
        return self.inodes[curr_ino]