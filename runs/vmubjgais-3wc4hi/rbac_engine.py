import functools

# Simulação de um contexto de usuário (normalmente viria do JWT/Sessão)
class User:
    def __init__(self, id, roles):
        self.id = id
        self.roles = roles  # Lista de papéis

# Banco de dados de permissões (Simulado)
PERMISSIONS_DB = {
    "admin": ["user:create", "user:delete", "report:view"],
    "editor": ["report:view"]
}

def check_permission(required_permission):
    """Decorador para validar permissões de forma declarativa."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(user, *args, **kwargs):
            # Resolve permissões do usuário baseado em seus papéis
            user_permissions = set()
            for role in user.roles:
                user_permissions.update(PERMISSIONS_DB.get(role, []))
            
            if required_permission not in user_permissions:
                # O "porquê": 403 é para acesso negado, 401 seria para não autenticado
                raise PermissionError(f"Acesso negado: Requer {required_permission}")
            
            return func(user, *args, **kwargs)
        return wrapper
    return decorator

# --- Exemplo de uso ---

@check_permission("user:delete")
def delete_user(user, target_id):
    return f"Usuário {target_id} deletado com sucesso."

# Teste de comportamento
admin = User(1, ["admin"])
guest = User(2, ["editor"])

print("--- Teste de RBAC ---")
try:
    print(delete_user(admin, 99))
    print(delete_user(guest, 99))
except PermissionError as e:
    print(f"Erro capturado: {e}")