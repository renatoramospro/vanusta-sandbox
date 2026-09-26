import os
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

    def _hash_object(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def _write_object(self, data: bytes) -> str:
        obj_id = self._hash_object(data)
        path = os.path.join(self.objects_dir, obj_id[:2], obj_id[2:])
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
        return obj_id

    def _read_object(self, obj_id: str) -> bytes:
        path = os.path.join(self.objects_dir, obj_id[:2], obj_id[2:])
        with open(path, "rb") as f:
            return f.read()

    def _get_head(self) -> str:
        with open(self.head_file, "r") as f:
            content = f.read().strip()
        if content.startswith("ref: "):
            ref_name = content[5:]
            ref_path = os.path.join(self.root_dir, ".vcs", ref_name)
            if os.path.exists(ref_path):
                with open(ref_path, "r") as rf:
                    return rf.read().strip()
            return ""
        return content

    def _set_head(self, branch_name: str):
        with open(self.head_file, "w") as f:
            f.write(f"ref: refs/heads/{branch_name}")

    def _get_branch_commit(self, branch_name: str) -> Optional[str]:
        ref_path = os.path.join(self.refs_dir, branch_name)
        if os.path.exists(ref_path):
            with open(ref_path, "r") as f:
                return f.read().strip()
        return None

    def _set_branch_commit(self, branch_name: str, commit_id: str):
        ref_path = os.path.join(self.refs_dir, branch_name)
        os.makedirs(os.path.dirname(ref_path), exist_ok=True)
        with open(ref_path, "w") as f:
            f.write(commit_id)

    def branch(self, name: str):
        current_commit = self._get_head()
        self._set_branch_commit(name, current_commit)

    def checkout(self, name: str):
        branch_path = os.path.join(self.refs_dir, name)
        if not os.path.exists(branch_path):
            raise ValueError(f"Branch {name} não existe.")
        self._set_head(name)
        commit_id = self._get_head()
        if commit_id:
            self._restore_commit(commit_id)

    def _restore_commit(self, commit_id: str):
        commit_data = json.loads(self._read_object(commit_id).decode("utf-8"))
        tree_id = commit_data["tree"]
        tree_data = json.loads(self._read_object(tree_id).decode("utf-8"))
        
        # Remove arquivos rastreados antigos do diretório de trabalho (exceto .vcs)
        for item in os.listdir(self.root_dir):
            if item == ".vcs":
                continue
            path = os.path.join(self.root_dir, item)
            if os.path.isfile(path):
                os.remove(path)

        for filename, file_obj_id in tree_data.items():
            content = self._read_object(file_obj_id)
            filepath = os.path.join(self.root_dir, filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "wb") as f:
                f.write(content)

    def commit(self, message: str, files_content: Dict[str, str]) -> str:
        tree = {}
        for filename, content in files_content.items():
            data = content.encode("utf-8")
            obj_id = self._write_object(data)
            tree[filename] = obj_id
        
        tree_data = json.dumps(tree, sort_keys=True).encode("utf-8")
        tree_id = self._write_object(tree_data)

        parent_commit = self._get_head()
        parents = [parent_commit] if parent_commit else []

        commit_obj = {
            "message": message,
            "tree": tree_id,
            "parents": parents
        }
        commit_data = json.dumps(commit_obj, sort_keys=True).encode("utf-8")
        commit_id = self._write_object(commit_data)

        # Atualiza a branch atual
        with open(self.head_file, "r") as f:
            content = f.read().strip()
        if content.startswith("ref: "):
            branch_ref = content[5:]
            ref_path = os.path.join(self.root_dir, ".vcs", branch_ref)
            with open(ref_path, "w") as rf:
                rf.write(commit_id)

        return commit_id

    def _get_commit_tree(self, commit_id: str) -> Dict[str, str]:
        if not commit_id:
            return {}
        commit_data = json.loads(self._read_object(commit_id).decode("utf-8"))
        tree_id = commit_data["tree"]
        return json.loads(self._read_object(tree_id).decode("utf-8"))

    def _find_lca(self, commit_a: str, commit_b: str) -> Optional[str]:
        ancestors_a = set()
        queue = [commit_a]
        while queue:
            curr = queue.pop(0)
            if curr in ancestors_a:
                continue
            ancestors_a.add(curr)
            commit_data = json.loads(self._read_object(curr).decode("utf-8"))
            queue.extend(commit_data.get("parents", []))

        queue = [commit_b]
        visited_b = set()
        while queue:
            curr = queue.pop(0)
            if curr in visited_b:
                continue
            if curr in ancestors_a:
                return curr
            visited_b.add(curr)
            commit_data = json.loads(self._read_object(curr).decode("utf-8"))
            queue.extend(commit_data.get("parents", []))
        return None

    def merge(self, target_branch: str) -> Tuple[bool, dict]:
        current_branch_ref = open(self.head_file).read().strip()[5:]
        current_commit = self._get_branch_commit(current_branch_ref.split("/")[-1])
        target_commit = self._get_branch_commit(target_branch)

        base_commit = self._find_lca(current_commit, target_commit)
        
        base_tree = self._get_commit_tree(base_commit)
        curr_tree = self._get_commit_tree(current_commit)
        target_tree = self._get_commit_tree(target_commit)

        all_files = set(base_tree.keys()) | set(curr_tree.keys()) | set(target_tree.keys())
        new_tree = {}
        conflicts = {}

        for filename in all_files:
            b_val = base_tree.get(filename)
            c_val = curr_tree.get(filename)
            t_val = target_tree.get(filename)

            if c_val == t_val:
                if c_val:
                    new_tree[filename] = c_val
            elif c_val == b_val:
                if t_val:
                    new_tree[filename] = t_val
            elif t_val == b_val:
                if c_val:
                    new_tree[filename] = c_val
            else:
                conflicts[filename] = (c_val, t_val)

        if conflicts:
            return False, {"conflicts": conflicts}

        # Cria commit de merge
        tree_data = json.dumps(new_tree, sort_keys=True).encode("utf-8")
        tree_id = self._write_object(tree_data)
        
        commit_obj = {
            "message": f"Merge branch '{target_branch}'",
            "tree": tree_id,
            "parents": [current_commit, target_commit]
        }
        commit_id = self._write_object(json.dumps(commit_obj, sort_keys=True).encode("utf-8"))
        self._set_branch_commit(current_branch_ref.split("/")[-1], commit_id)
        self._restore_commit(commit_id)

        return True, {"commit_id": commit_id}


def test_vcs_lifecycle():
    repo_path = "./test_repo"
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path)

    vcs = SimpleVCS(repo_path)

    # 1. Commit inicial na main
    c1 = vcs.commit("Commit 1", {"README.md": "Hello World\n", "main.py": "print(1)\n"})
    print(f"Commit 1 criado: {c1}")

    # Validação automatizada de integridade do objeto commit e árvores
    commit_bytes = vcs._read_object(c1)
    assert vcs._hash_object(commit_bytes) == c1, "Integridade do commit corrompida!"
    print("Validação de integridade SHA-256 do commit 1: OK")

    # 2. Criar branch feature e divergir (feature altera main.py, main altera README.md)
    vcs.branch("feature")
    vcs.checkout("feature")
    c2 = vcs.commit("Commit 2 (feature)", {"README.md": "Hello World\n", "main.py": "print('feature')\n"})
    print(f"Commit 2 (feature) criado: {c2}")

    vcs.checkout("main")
    c3 = vcs.commit("Commit 3 (main divergente)", {"README.md": "Hello Main\n", "main.py": "print(1)\n"})
    print(f"Commit 3 (main divergente) criado: {c3}")

    # 3. Merge limpo de três vias (sem conflito: feature alterou main.py, main alterou README.md)
    success, result = vcs.merge("feature")
    print(f"Resultado do Merge Limpo: success={success}, result={result}")
    assert success is True, "O merge de três vias limpo deveria ter tido sucesso!"

    # Validar integridade do commit de merge (deve ter 2 pais)
    merge_commit_obj = json.loads(vcs._read_object(result["commit_id"]).decode("utf-8"))
    print(f"Pais do commit de merge: {merge_commit_obj['parents']}")
    assert len(merge_commit_obj["parents"]) == 2

    # --- Demonstração de Contraexemplo: Conflito de Merge ---
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path)
    
    vcs2 = SimpleVCS(repo_path)
    base_c = vcs2.commit("Base", {"file.txt": "linha comum\n"})
    
    vcs2.branch("branch1")
    vcs2.branch("branch2")

    vcs2.checkout("branch1")
    vcs2.commit("Mod 1", {"file.txt": "alteracao branch 1\n"})

    vcs2.checkout("branch2")
    vcs2.commit("Mod 2", {"file.txt": "alteracao branch 2\n"})

    # Tentar fundir branch1 na branch2 deve gerar conflito no mesmo arquivo
    success_cf, result_cf = vcs2.merge("branch1")
    print(f"Teste de Conflito - Sucesso? {success_cf}, Conflitos detectados: {result_cf.get('conflicts')}")
    assert success_cf is False, "Deveria ter detectado conflito e falhado o merge!"
    assert "file.txt" in result_cf["conflicts"]

    print("Todos os testes do motor VCS baseado em DAG passaram com sucesso!")
    shutil.rmtree(repo_path)

if __name__ == "__main__":
    test_vcs_lifecycle()