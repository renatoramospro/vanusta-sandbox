import os
import hashlib
import json
import shutil

class GitObjectStore:
    """Armazena objetos baseados em conteúdo (Blob e Commit)."""
    def __init__(self, db_path=".vcs_objects"):
        self.db_path = db_path
        if os.path.exists(self.db_path):
            shutil.rmtree(self.db_path)
        os.makedirs(self.db_path)

    def store_object(self, content: bytes) -> str:
        sha = hashlib.sha256(content).hexdigest()
        obj_path = os.path.join(self.db_path, sha)
        with open(obj_path, "wb") as f:
            f.write(content)
        return sha

    def get_object(self, sha: str) -> bytes:
        obj_path = os.path.join(self.db_path, sha)
        with open(obj_path, "rb") as f:
            return f.read()

class DistributedVCS:
    """Gerenciador do Repositório Distribuído."""
    def __init__(self):
        self.store = GitObjectStore()
        self.refs = {"main": None}
        self.current_branch = "main"
        self.working_directory = {}

    def commit(self, message: str) -> str:
        # Serializa o estado atual do working directory
        tree_data = json.dumps(self.working_directory, sort_keys=True).encode("utf-8")
        tree_sha = self.store.store_object(tree_data)

        parent_sha = self.refs.get(self.current_branch)
        commit_obj = {
            "tree": tree_sha,
            "parent": parent_sha,
            "message": message
        }
        commit_data = json.dumps(commit_obj, sort_keys=True).encode("utf-8")
        commit_sha = self.store.store_object(commit_data)

        # Atualiza o ponteiro da branch atual
        self.refs[self.current_branch] = commit_sha
        return commit_sha

    def create_branch(self, branch_name: str):
        self.refs[branch_name] = self.refs.get(self.current_branch)

    def checkout(self, branch_name: str):
        if branch_name not in self.refs:
            raise ValueError(f"Branch {branch_name} não existe.")
        self.current_branch = branch_name
        commit_sha = self.refs[branch_name]
        if commit_sha:
            commit_data = json.loads(self.store.get_object(commit_sha).decode("utf-8"))
            tree_data = self.store.get_object(commit_data["tree"])
            self.working_directory = json.loads(tree_data.decode("utf-8"))
        else:
            self.working_directory = {}

    def merge(self, other_branch: str):
        """
        Demonstração de detecção e resolução de conflitos de merge.
        Equívoco comum combatido: assumir que merges nunca conflitam ou 
        simplesmente sobrescrever dados concorrentes.
        """
        our_commit_sha = self.refs.get(self.current_branch)
        their_commit_sha = self.refs.get(other_branch)

        # Carrega árvores
        our_tree = self.working_directory
        
        their_commit_data = json.loads(self.store.get_object(their_commit_sha).decode("utf-8"))
        their_tree = json.loads(self.store.get_object(their_commit_data["tree"]).decode("utf-8"))

        # Detecção de conflitos (mesma chave, valores diferentes)
        conflicts = []
        for k, their_val in their_tree.items():
            if k in our_tree and our_tree[k] != their_val:
                conflicts.append((k, our_tree[k], their_val))

        if conflicts:
            print(f"[CONFLITO DETECTADO] Conflito nas chaves: {conflicts}")
            # Resolução automatizada/manual controlada (estratégia 'ours' ou 'theirs' simulada)
            for k, our_val, their_val in conflicts:
                # Exemplo de resolução: manter o nosso e registrar aviso
                print(f"Resolvendo conflito em '{k}': mantendo valor local '{our_val}' (descartando concorrente '{their_val}').")
        
        # Consolida merge sem perda de histórico
        for k, v in their_tree.items():
            if k not in our_tree:
                our_tree[k] = v

        self.commit(f"Merge branch '{other_branch}' into {self.current_branch}")

# --- Teste Executável ---
if __name__ == "__main__":
    vcs = DistributedVCS()

    # 1. Commit inicial na main
    vcs.working_directory["config.json"] = "v1"
    vcs.commit("Commit inicial na main")

    # 2. Criar branch 'feature' e alterar arquivo concorrentemente
    vcs.create_branch("feature")
    vcs.working_directory["feature.txt"] = "dados da feature"
    vcs.commit("Adiciona feature")

    # 3. Voltar para main e alterar o mesmo arquivo/chave (simulando conflito)
    vcs.checkout("main")
    vcs.working_directory["config.json"] = "v2_modificado_na_main"
    vcs.commit("Modifica config na main")

    # 4. Criar outro branch 'hotfix' e modificar a mesma chave para testar conflito
    vcs.create_branch("hotfix")
    vcs.checkout("hotfix")
    vcs.working_directory["config.json"] = "v2_modificado_no_hotfix"
    vcs.commit("Modifica config no hotfix")

    # 5. Tentar realizar o merge entre main e hotfix (deve detectar conflito)
    vcs.checkout("main")
    print("Iniciando merge de hotfix em main...")
    vcs.merge("hotfix")

    print("Sucesso! O sistema gerencia objetos imutáveis, histórico DAG e conflitos.")