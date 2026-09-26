import threading
import time
from typing import Dict, List, Optional, Tuple

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
        self.entries: Dict[str, int] = {} if is_dir else None
        self.lock = threading.RLock()

class VirtualFileSystem:
    def __init__(self):
        self.lock = threading.RLock()
        self.inodes: Dict[int, Inode] = {}
        self.next_ino = 1
        self.cwd = "/"
        
        root_inode = self._alloc_inode(is_dir=True)
        self.root_ino = root_inode.ino
        self.inodes[self.root_ino] = root_inode

    def _alloc_inode(self, is_dir: bool, permissions: int = 0o755) -> Inode:
        with self.lock:
            ino = self.next_ino
            self.next_ino += 1
            inode = Inode(ino, is_dir, permissions)
            self.inodes[ino] = inode
            return inode

    def _resolve_path(self, path: str) -> Tuple[Inode, str]:
        if not path.startswith("/"):
            # Resolução baseada em cwd
            if self.cwd == "/":
                full_path = "/" + path
            else:
                full_path = self.cwd + "/" + path
        else:
            full_path = path

        parts = []
        for p in full_path.split("/"):
            if not p or p == ".":
                continue
            elif p == "..":
                if parts:
                    parts.pop()
            else:
                parts.append(p)

        current = self.inodes[self.root_ino]
        for i, part in enumerate(parts):
            with current.lock:
                if not current.is_dir:
                    raise NotADirectory(f"Componente intermediário não é diretório: {part}")
                if part not in current.entries:
                    if i == len(parts) - 1:
                        return current, ""
                    raise FileNotFound(f"Caminho não encontrado: {part}")
                
                next_ino = current.entries[part]
                current = self.inodes[next_ino]

        return current, parts[-1] if parts else ""

    def chdir(self, path: str):
        inode, name = self._resolve_path(path)
        # Se for um caminho completo para diretório
        target = inode
        if name:
            if name not in inode.entries:
                raise FileNotFound(path)
            target = self.inodes[inode.entries[name]]
        
        if not target.is_dir:
            raise NotADirectory(path)
        
        # Reconstrói o caminho absoluto do cwd
        # Para simplificar, armazenamos se for absoluto ou resolvemos
        if path.startswith("/"):
            self.cwd = path
        else:
            if self.cwd == "/":
                self.cwd = "/" + path
            else:
                self.cwd = self.cwd + "/" + path
        
        # Normaliza cwd
        parts = [p for p in self.cwd.split("/") if p and p != "."]
        resolved = []
        for p in parts:
            if p == "..":
                if resolved:
                    resolved.pop()
            else:
                resolved.append(p)
        self.cwd = "/" + "/".join(resolved)

    def create_file(self, path: str, permissions: int = 0o644):
        parent, name = self._resolve_path(path)
        if not name:
            raise FileSystemError("Nome de arquivo inválido")
        with parent.lock:
            if name in parent.entries:
                raise FileExists(path)
            new_inode = self._alloc_inode(is_dir=False, permissions=permissions)
            parent.entries[name] = new_inode.ino
            parent.modified_at = time.time()

    def mkdir(self, path: str, permissions: int = 0o755):
        parent, name = self._resolve_path(path)
        if not name:
            raise FileSystemError("Nome de diretório inválido")
        with parent.lock:
            if name in parent.entries:
                raise FileExists(path)
            new_inode = self._alloc_inode(is_dir=True, permissions=permissions)
            parent.entries[name] = new_inode.ino
            parent.modified_at = time.time()

    def read_file(self, path: str) -> bytes:
        parent, name = self._resolve_path(path)
        if not name:
            inode = parent
        else:
            if name not in parent.entries:
                raise FileNotFound(path)
            inode = self.inodes[parent.entries[name]]
        
        with inode.lock:
            if inode.is_dir:
                raise IsADirectory(path)
            inode.accessed_at = time.time()
            return bytes(inode.data)

    def write_file(self, path: str, data: bytes, offset: int = 0):
        parent, name = self._resolve_path(path)
        if not name:
            inode = parent
        else:
            if name not in parent.entries:
                raise FileNotFound(path)
            inode = self.inodes[parent.entries[name]]
        
        with inode.lock:
            if inode.is_dir:
                raise IsADirectory(path)
            
            end_pos = offset + len(data)
            if end_pos > len(inode.data):
                inode.data.extend(b'\x00' * (end_pos - len(inode.data)))
            
            inode.data[offset:end_pos] = data
            inode.size = len(inode.data)
            inode.modified_at = time.time()

    def delete(self, path: str):
        parent, name = self._resolve_path(path)
        if not name:
            raise FileSystemError("Não é possível deletar a raiz")
        with parent.lock:
            if name not in parent.entries:
                raise FileNotFound(path)
            ino = parent.entries[name]
            inode = self.inodes[ino]
            with inode.lock:
                if inode.is_dir and len(inode.entries) > 0:
                    raise FileSystemError("Diretório não está vazio")
            del parent.entries[name]
            del self.inodes[ino]
            parent.modified_at = time.time()