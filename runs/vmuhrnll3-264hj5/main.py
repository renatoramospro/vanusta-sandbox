import os
import re
import hashlib
import json
import shutil
from typing import Dict, List, Optional, Tuple

class SimpleVCS:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.objects_dir = os.path.join(root_dir, ".vcs", "objects")
        self.refs_dir = os.path.join(root_dir, ".vcs", "refs", "heads")
        self.head_file = os.path.join(root_dir, ".vcs", "HEAD")
        
        os.makedirs(self.objects_dir, exist_ok=True)
        os.makedirs(self.refs_dir, exist_ok=True)
        
        if not os.path.exists(self.head_file):
            self._set_head("main")

    def _validate_hex_id(self, obj_id: str) -> str:
        """Garante que o ID do objeto é um SHA-256 válido (64 caracteres hexadecimais),
        evitando ataques de path traversal ou injeção de caminhos."""
        if not isinstance(obj_id, str) or not re.match(r"^[0-9a-fA-F]{64}$", obj_id):
            raise ValueError(f"ID de objeto inválido ou malformado (potencial travessia de caminho): {obj_id}")
        return obj_id.lower()

    def _validate_ref_name(self, name: str) -> str:
        """Valida nomes de branches/referências para evitar caracteres perigosos."""
        if not isinstance(name, str) or not re.match(r"^[a-zA-Z0-9_\-/]+$", name) or ".." in name:
            raise ValueError(f"Nome de referência inválido: {name}")
        return name

    def _hash_object(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def _write_object(self, data: bytes) -> str:
        obj_id = self._hash_object(data)
        self._validate_hex_id(obj_id)
        path = os.path.join(self.objects_dir, obj_id[:2], obj_id[2:])
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
        return obj_id

    def _read_object(self, obj_id: str) -> bytes:
        self._validate_hex_id(obj_id)
        path = os.path.join(self.objects_dir, obj_id[:2], obj_id[2:])
        if not os.path.abspath(path).startswith(os.path.abspath(self.objects_dir)):
            raise PermissionError("Acesso negado: tentativa de leitura fora do repositório de objetos.")
        with open(path, "rb") as f:
            return f.read()

    def _verify_tree_integrity(self, tree_id: str) -> bool:
        """Recalcula e valida profundamente o SHA-256 de cada blob na árvore."""
        self._validate_hex_id(tree_id)
        tree_data = self._read_object(tree_id)
        tree_obj = json.loads(tree_data.decode("utf-8"))
        
        for filename, blob_id in tree_obj.items():
            self._validate_hex_id(blob_id)
            blob_content = self._read_object(blob_id)
            recalculated_hash = self._hash_object(blob_content)
            if recalculated_hash != blob_id:
                raise ValueError(f"Violação de integridade detectada! O blob para '{filename}' foi adulterado. "
                                 f"Esperado: {blob_id}, Obtido: {recalculated_hash}")
        return True

    def _get_head(self) -> str:
        with open(self.head_file, "r") as f:
            content = f.read().strip()
        if content.startswith("ref: "):
            ref_name = content[5:]
            self._validate_ref_name(ref_name)
            ref_path = os.path.join(self.root_dir, ".vcs", ref_name)
            if os.path.exists(ref_path):
                with open(ref_path, "r") as rf:
                    return rf.read().strip()
            return ""
        return content

    def _set_head(self, ref_or_commit: str):
        if ref_or_commit in ["main"] or not re.match(r"^[0-9a-f]{64}$", ref_or_commit):
            safe_ref = self._validate_ref_name(ref_or_commit)
            content = f"ref: refs/heads/{safe_ref}"
        else:
            content = self._validate_hex_id(ref_or_commit)
        
        with open(self.head_file, "w") as f:
            f.write(content)

    def _get_branch_ref_path(self, branch_name: str) -> str:
        safe_name = self._validate_ref_name(branch_name)
        return os.path.join(self.refs_dir, safe_name)

    def branch(self, branch_name: str):
        safe_name = self._validate_ref_name(branch_name)
        current_commit = self._get_head()
        ref_path = self._get_branch_ref_path(safe_name)
        with open(ref_path, "w") as f:
            f.write(current_commit)

    def checkout(self, branch_name: str):
        safe_name = self._validate_ref_name(branch_name)
        ref_path = self._get_branch_ref_path(safe_name)
        if not os.path.exists(ref_path):
            raise ValueError(f"Branch '{safe_name}' não existe.")
        with open(self.head_file, "w") as f:
            f.write(f"ref: refs/heads/{safe_name}")
        
        commit_id = self._get_head()
        if commit_id:
            self.restore_commit(commit_id)

    def restore_commit(self, commit_id: str):
        self._validate_hex_id(commit_id)
        commit_data = self._read_object(commit_id)
        commit_obj = json.loads(commit_data.decode("utf-8"))
        tree_id = commit_obj["tree"]
        
        # Validação profunda de integridade da árvore e dos blobs
        self._verify_tree_integrity(tree_id)
        
        tree_data = self._read_object(tree_id)
        tree_obj = json.loads(tree_data.decode("utf-8"))
        
        for filename, blob_id in tree_obj.items():
            file_path = os.path.join(self.root_dir, filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            blob_content = self._read_object(blob_id)
            with open(file_path, "wb") as f:
                f.write(blob_content)

    def commit(self, message: str, files: Dict[str, str]) -> str:
        tree = {}
        for filename, content in files.items():
            if ".." in filename or filename.startswith("/"):
                raise ValueError(f"Nome de arquivo inválido: {filename}")
            blob_id = self._write_object(content.encode("utf-8"))
            tree[filename] = blob_id
        
        tree_data = json.dumps(tree, sort_keys=True).encode("utf-8")
        tree_id = self._write_object(tree_data)
        
        parents = []
        current_commit = self._get_head()
        if current_commit:
            parents.append(current_commit)
        
        commit_obj = {
            "tree": tree_id,
            "parents": parents,
            "message": message
        }
        commit_data = json.dumps(commit_obj, sort_keys=True).encode("utf-8")
        commit_id = self._write_object(commit_data)
        
        # Atualizar ponteiro da branch atual ou HEAD destacada
        with open(self.head_file, "r") as f:
            head_content = f.read().strip()
        
        if head_content.startswith("ref: "):
            ref_name = head_content[5:]
            ref_path = os.path.join(self.root_dir, ".vcs", ref_name)
            with open(ref_path, "w") as rf:
                rf.write(commit_id)
        else:
            self._set_head(commit_id)
            
        return commit_id

    def _get_commit_history(self, commit_id: str) -> List[str]:
        history = []
        queue = [commit_id]
        visited = set()
        while queue:
            cid = queue.pop(0)
            if cid in visited:
                continue
            visited.add(cid)
            history.append(cid)
            try:
                commit_data = self._read_object(cid)
                commit_obj = json.loads(commit_data.decode("utf-8"))
                for p in commit_obj.get("parents", []):
                    if p not in visited:
                        queue.append(p)
            except Exception:
                pass
        return history

    def _find_lca(self, commit_a: str, commit_b: str) -> Optional[str]:
        history_a = set(self._get_commit_history(commit_a))
        queue = [commit_b]
        visited = set()
        while queue:
            cid = queue.pop(0)
            if cid in history_a:
                return cid
            if cid in visited:
                continue
            visited.add(cid)
            try:
                commit_data = self._read_object(cid)
                commit_obj = json.loads(commit_data.decode("utf-8"))
                for p in commit_obj.get("parents", []):
                    queue.append(p)
            except Exception:
                pass
        return None

    def _get_tree_files(self, commit_id: str) -> Dict[str, str]:
        if not commit_id:
            return {}
        commit_data = self._read_object(commit_id)
        commit_obj = json.loads(commit_data.decode("utf-8"))
        tree_id = commit_obj["tree"]
        self._verify_tree_integrity(tree_id)
        tree_data = self._read_object(tree_id)
        return json.loads(tree_data.decode("utf-8"))

    def merge(self, branch_name: str) -> Tuple[bool, dict]:
        safe_branch = self._validate_ref_name(branch_name)
        current_commit = self._get_head()
        ref_path = self._get_branch_ref_path(safe_branch)
        if not os.path.exists(ref_path):
            raise ValueError(f"Branch '{safe_branch}' não existe.")
        with open(ref_path, "r") as f:
            target_commit = f.read().strip()
        
        base_commit = self._find_lca(current_commit, target_commit)
        
        base_files = self._get_tree_files(base_commit) if base_commit else {}
        current_files = self._get_tree_files(current_commit)
        target_files = self._get_tree_files(target_commit)
        
        merged_files = {}
        conflicts = {}
        
        all_files = set(base_files.keys()) | set(current_files.keys()) | set(target_files.keys())
        
        for filename in all_files:
            b_blob = base_files.get(filename)
            c_blob = current_files.get(filename)
            t_blob = target_files.get(filename)
            
            if c_blob == t_blob:
                if c_blob is not None:
                    merged_files[filename] = c_blob
            elif b_blob == c_blob:
                if t_blob is not None:
                    merged_files[filename] = t_blob
            elif b_blob == t_blob:
                if c_blob is not None:
                    merged_files[filename] = c_blob
            else:
                if c_blob != t_blob:
                    conflicts[filename] = (c_blob, t_blob)
                else:
                    if c_blob is not None:
                        merged_files[filename] = c_blob

        if conflicts:
            return False, {"conflicts": conflicts}
        
        tree_data = json.dumps(merged_files, sort_keys=True).encode("utf-8")
        tree_id = self._write_object(tree_data)
        
        commit_obj = {
            "tree": tree_id,
            "parents": [current_commit, target_commit],
            "message": f"Merge branch '{safe_branch}'"
        }
        commit_data = json.dumps(commit_obj, sort_keys=True).encode("utf-8")
        commit_id = self._write_object(commit_data)
        
        with open(self.head_file, "r") as f:
            head_content = f.read().strip()
        if head_content.startswith("ref: "):
            ref_name = head_content[5:]
            ref_path = os.path.join(self.root_dir, ".vcs", ref_name)
            with open(ref_path, "w") as rf:
                rf.write(commit_id)
        else:
            self._set_head(commit_id)
            
        self.restore_commit(commit_id)
        return True, {"commit_id": commit_id}

def test_vcs_security_and_integrity():
    repo_path = "./test_repo_sec"
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path)
        
    vcs = SimpleVCS(repo_path)
    
    # 1. Teste de validação de IDs maliciosos (Path Traversal prevention)
    try:
        vcs._read_object("../etc/passwd")
        assert False, "Deveria ter rejeitado ID malicioso!"
    except ValueError as e:
        print(f"Segurança validada - ID malicioso rejeitado corretamente: {e}")

    try:
        vcs._validate_ref_name("branch/../../evil")
        assert False, "Deveria ter rejeitado referência maliciosa!"
    except ValueError as e:
        print(f"Segurança validada - Referência maliciosa rejeitada corretamente: {e}")

    # 2. Teste de ciclo de vida com verificação profunda de integridade de blob
    c1 = vcs.commit("Initial", {"main.py": "print('hello')\n"})
    print(f"Commit 1 criado e validado por integridade SHA-256 profunda: {c1}")

    # Simular adulteração maliciosa de blob em disco
    commit_data = json.loads(vcs._read_object(c1).decode("utf-8"))
    tree_data = json.loads(vcs._read_object(commit_data["tree"]).decode("utf-8"))
    blob_id_main = tree_data["main.py"]
    
    # Reescrever o arquivo blob fisicamente com conteúdo adulterado mantendo o mesmo nome
    blob_path = os.path.join(repo_path, ".vcs", "objects", blob_id_main[:2], blob_id_main[2:])
    with open(blob_path, "wb") as f:
        f.write(b"print('adulterado')\n")

    # Tentar restaurar o commit deve disparar o alarme de integridade profunda
    try:
        vcs.restore_commit(c1)
        assert False, "Deveria ter detectado a adulteração do blob!"
    except ValueError as e:
        print(f"Validação de integridade profunda funcionou com sucesso contra adulteração: {e}")

    shutil.rmtree(repo_path)
    print("Todos os testes de segurança e integridade profunda passaram com sucesso!")

if __name__ == "__main__":
    test_vcs_security_and_integrity()