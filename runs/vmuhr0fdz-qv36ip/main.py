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
        path = os.path.join(self.objects_dir, obj_id)
        if not os.path.exists(path):
            with open(path, "wb") as f:
                f.write(data)
        return obj_id

    def _read_object(self, obj_id: str) -> bytes:
        path = os.path.join(self.objects_dir, obj_id)
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
        return content  # Detached HEAD

    def _set_head(self, branch_name: str):
        with open(self.head_file, "w") as f:
            f.write(f"ref: refs/heads/{branch_name}")

    def get_branch_commit(self, branch_name: str) -> Optional[str]:
        ref_path = os.path.join(self.refs_dir, branch_name)
        if os.path.exists(ref_path):
            with open(ref_path, "r") as f:
                return f.read().strip()
        return None

    def _set_branch_commit(self, branch_name: str, commit_id: str):
        ref_path = os.path.join(self.refs_dir, branch_name)
        with open(ref_path, "w") as f:
            f.write(commit_id)

    def commit(self, message: str, files: Dict[str, str]) -> str:
        """Cria um commit contendo o estado dos arquivos e o aponta para o DAG."""
        tree = {}
        for filepath, content in files.items():
            obj_id = self._write_object(content.encode("utf-8"))
            tree[filepath] = obj_id

        parent_id = self.get_head_commit()
        commit_data = {
            "message": message,
            "parents": [parent_id] if parent_id else [],
            "tree": tree
        }
        commit_bytes = json.dumps(commit_data, sort_keys=True).encode("utf-8")
        commit_id = self._write_object(commit_bytes)

        current_branch = self._get_current_branch_name()
        if current_branch:
            self._set_branch_commit(current_branch, commit_id)
        else:
            # Detached head update not fully implemented for brevity, assume branch
            pass
        return commit_id

    def get_head_commit(self) -> Optional[str]:
        current_branch = self._get_current_branch_name()
        if current_branch:
            return self.get_branch_commit(current_branch)
        return None

    def _get_current_branch_name(self) -> Optional[str]:
        with open(self.head_file, "r") as f:
            content = f.read().strip()
        if content.startswith("ref: refs/heads/"):
            return content[16:]
        return None

    def branch(self, branch_name: str):
        """Cria uma nova ramificação apontando para o commit atual (O(1) no DAG)."""
        current_commit = self.get_head_commit()
        if current_commit:
            self._set_branch_commit(branch_name, current_commit)
        else:
            # Se o repositório estiver vazio, cria branch sem commit inicial
            pass

    def checkout(self, branch_name: str):
        """Muda o HEAD para a ramificação especificada."""
        self._set_head(branch_name)

    def find_lca(self, commit_a: str, commit_b: str) -> Optional[str]:
        """Encontra o ancestral comum mais baixo (Lowest Common Ancestor) no DAG."""
        visited_a = set()
        queue = [commit_a]
        while queue:
            c = queue.pop(0)
            if c in visited_a:
                continue
            visited_a.add(c)
            commit_data = json.loads(self._read_object(c).decode("utf-8"))
            queue.extend(commit_data.get("parents", []))

        queue = [commit_b]
        visited_b = set()
        while queue:
            c = queue.pop(0)
            if c in visited_b:
                continue
            if c in visited_a:
                return c  # Encontrou LCA
            visited_b.add(c)
            commit_data = json.loads(self._read_object(c).decode("utf-8"))
            queue.extend(commit_data.get("parents", []))
        return None

    def get_commit_tree(self, commit_id: str) -> Dict[str, str]:
        commit_data = json.loads(self._read_object(commit_id).decode("utf-8"))
        return commit_data["tree"]

    def merge(self, branch_name: str) -> Tuple[bool, Dict[str, str]]:
        """Realiza merge de três vias entre o HEAD atual e branch_name."""
        head_commit_id = self.get_head_commit()
        other_commit_id = self.get_branch_commit(branch_name)

        if not head_commit_id or not other_commit_id:
            return False, {"error": "Commits insuficientes para merge"}

        lca_id = self.find_lca(head_commit_id, other_commit_id)
        if not lca_id:
            return False, {"error": "Nenhum ancestral comum encontrado"}

        base_tree = self.get_commit_tree(lca_id)
        head_tree = self.get_commit_tree(head_commit_id)
        other_tree = self.get_commit_tree(other_commit_id)

        all_files = set(base_tree.keys()) | set(head_tree.keys()) | set(other_tree.keys())
        merged_tree = {}
        conflicts = {}

        for f in all_files:
            b_val = base_tree.get(f)
            h_val = head_tree.get(f)
            o_val = other_tree.get(f)

            if h_val == o_val:
                if h_val:
                    merged_tree[f] = h_val
            elif h_val == b_val:
                if o_val:
                    merged_tree[f] = o_val
            elif o_val == b_val:
                if h_val:
                    merged_tree[f] = h_val
            else:
                # Conflito real de três vias
                conflicts[f] = (h_val, o_val)

        if conflicts:
            return False, {"conflicts": conflicts}

        # Cria commit de merge com 2 pais
        merge_commit_data = {
            "message": f"Merge branch '{branch_name}'",
            "parents": [head_commit_id, other_commit_id],
            "tree": merged_tree
        }
        commit_bytes = json.dumps(merge_commit_data, sort_keys=True).encode("utf-8")
        commit_id = self._write_object(commit_bytes)
        
        current_branch = self._get_current_branch_name()
        self._set_branch_commit(current_branch, commit_id)
        return True, {"commit_id": commit_id}

# --- Testes e Demonstração Automatizada ---
def test_vcs_lifecycle():
    repo_path = "./test_repo"
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path)

    vcs = SimpleVCS(repo_path)

    # 1. Commit inicial na main
    c1 = vcs.commit("Initial commit", {"README.md": "# Projeto"})
    print(f"Commit 1 criado: {c1}")
    assert c1 is not None

    # 2. Criar branch 'feature' e alternar para ela
    vcs.branch("feature")
    vcs.checkout("feature")
    assert vcs._get_current_branch_name() == "feature"

    # 3. Commit na feature
    c2 = vcs.commit("Add feature code", {"README.md": "# Projeto\nFeature X", "app.py": "print('hello')"})
    print(f"Commit 2 (feature) criado: {c2}")

    # 4. Voltar para main e fazer alteração divergente
    vcs.checkout("main")
    assert vcs._get_current_branch_name() == "main"
    c3 = vcs.commit("Update readme in main", {"README.md": "# Projeto\nMain update"})
    print(f"Commit 3 (main divergente) criado: {c3}")

    # 5. Testar Merge de Três Vias bem-sucedido (main funde feature)
    success, result = vcs.merge("feature")
    print(f"Resultado do Merge: success={success}, result={result}")
    assert success is True, "O merge de três vias deveria ter tido sucesso!"

    # Validar integridade do commit de merge (deve ter 2 pais)
    merge_commit_obj = json.loads(vcs._read_object(result["commit_id"]).decode("utf-8"))
    print(f"Pais do commit de merge: {merge_commit_obj['parents']}")
    assert len(merge_commit_obj["parents"]) == 2

    # --- Demonstração de Contraexemplo: Conflito de Merge ---
    # Vamos resetar e simular um conflito em que ambos alteram o mesmo arquivo de forma diferente
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

    # Tentar fundir branch1 na branch2 deve gerar conflito
    success_cf, result_cf = vcs2.merge("branch1")
    print(f"Teste de Conflito - Sucesso? {success_cf}, Conflitos detectados: {result_cf.get('conflicts')}")
    assert success_cf is False, "Deveria ter detectado conflito e falhado o merge!"
    assert "file.txt" in result_cf["conflicts"]

    print("Todos os testes do motor VCS baseado em DAG passaram com sucesso!")
    shutil.rmtree(repo_path)

if __name__ == "__main__":
    test_vcs_lifecycle()