import threading
import time
from typing import Dict, Tuple

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
        """
        Resolve um caminho para o Inode do diretório pai e o nome do arquivo/diretório final.
        """
        if not path:
            raise FileSystemError("Caminho vazio")
        
        if path.startswith("/"):
            current_inode = self.inodes[self.root_ino]
            parts = [p for p in path.split("/") if p and p != "."]
        else:
            # Caminho relativo a self.cwd
            current_inode = self._get_inode_by_absolute_path(self.cwd)
            parts = [p for p in path.split("/") if p and p != "."]
            
        # Processar diretórios intermediários
        for i, part in enumerate(parts[:-1]):
            if part == "..":
                # Sair da raiz não é permitido, fica na raiz
                # Para simplificar o cwd relativo, recalculamos a partir do root se necessário
                current_inode = self._navigate_up(current_inode)
                continue
                
            if not current_inode.is_dir:
                raise NotADirectory(f"Não é um diretório")
            
            with current_inode.lock:
                if part not in current_inode.entries:
                    raise FileNotFound(f"Diretório não encontrado: {part}")
                child_ino = current_inode.entries[part]
                current_inode = self.inodes[child_ino]

        if not parts:
            raise FileSystemError("Caminho inválido")
            
        target_name = parts[-1]
        if target_name == "..":
            raise FileSystemError("Nome de caminho inválido")
            
        return current_inode, target_name

    def _navigate_up(self, inode: Inode) -> Inode:
        # Busca o pai ou retorna o root se já estiver no root
        if inode.ino == self.root_ino:
            return inode
        for ino, candidate in self.inodes.items():
            if candidate.is_dir:
                for name, child_ino in candidate.entries.items():
                    if child_ino == inode.ino:
                        return candidate
        return self.inodes[self.root_ino]

    def _get_inode_by_absolute_path(self, path: str) -> Inode:
        if path == "/":
            return self.inodes[self.root_ino]
        current_inode = self.inodes[self.root_ino]
        parts = [p for p in path.split("/") if p and p != "."]
        for part in parts:
            if part == "..":
                current_inode = self._navigate_up(current_inode)
                continue
            if not current_inode.is_dir:
                raise NotADirectory("Não é um diretório")
            with current_inode.lock:
                if part not in current_inode.entries:
                    raise FileNotFound(f"Caminho não encontrado: {part}")
                current_inode = self.inodes[current_inode.entries[part]]
        return current_inode

    def create_file(self, path: str, permissions: int = 0o644) -> int:
        with self.lock:
            parent, name = self._resolve_path(path)
            if not parent.is_dir:
                raise NotADirectory("Pai não é um diretório")
            with parent.lock:
                if name in parent.entries:
                    raise FileExists(f"Arquivo já existe: {name}")
                new_inode = self._alloc_inode(is_dir=False, permissions=permissions)
                parent.entries[name] = new_inode.ino
                parent.modified_at = time.time()
                return new_inode.ino

    def mkdir(self, path: str, permissions: int = 0o755) -> int:
        with self.lock:
            parent, name = self._resolve_path(path)
            if not parent.is_dir:
                raise NotADirectory("Pai não é um diretório")
            with parent.lock:
                if name in parent.entries:
                    raise FileExists(f"Diretório já existe: {name}")
                new_inode = self._alloc_inode(is_dir=True, permissions=permissions)
                parent.entries[name] = new_inode.ino
                parent.modified_at = time.time()
                return new_inode.ino

    def read_file(self, path: str) -> bytes:
        parent, name = self._resolve_path(path)
        with parent.lock:
            if name not in parent.entries:
                raise FileNotFound(f"Arquivo não encontrado: {name}")
            inode = self.inodes[parent.entries[name]]
        
        with inode.lock:
            if inode.is_dir:
                raise IsADirectory("É um diretório")
            inode.accessed_at = time.time()
            return bytes(inode.data)

    def write_file(self, path: str, data: bytes, offset: int = 0):
        parent, name = self._resolve_path(path)
        with parent.lock:
            if name not in parent.entries:
                raise FileNotFound(f"Arquivo não encontrado: {name}")
            inode = self.inodes[parent.entries[name]]
        
        with inode.lock:
            if inode.is_dir:
                raise IsADirectory("É um diretório")
            
            required_size = offset + len(data)
            if required_size > len(inode.data):
                inode.data.extend(b'\x00' * (required_size - len(inode.data)))
            
            inode.data[offset:offset + len(data)] = data
            inode.size = len(inode.data)
            inode.modified_at = time.time()

    def delete(self, path: str):
        parent, name = self._resolve_path(path)
        with parent.lock:
            if name not in parent.entries:
                raise FileNotFound(f"Não encontrado: {name}")
            inode = self.inodes[parent.entries[name]]
            
            with inode.lock:
                if inode.is_dir and len(inode.entries) > 0:
                    raise FileSystemError("Diretório não está vazio")
            
            del parent.entries[name]
            del self.inodes[inode.ino]
            parent.modified_at = time.time()

    def chdir(self, path: str):
        inode = self._get_inode_by_absolute_path(path if path.startswith("/") else f"{self.cwd}/{path}")
        if not inode.is_dir:
            raise NotADirectory("Não é um diretório")
        # Normalizar cwd simples
        if path.startswith("/"):
            self.cwd = path
        else:
            # Simplificação para testes
            self.cwd = f"{self.cwd.rstrip('/')}/{path}"