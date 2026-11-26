from typing import Set, Dict, Optional, List

class Permission:
    def __init__(self, action: str, resource: str):
        self.action = action      # ex: 'read', 'write', 'delete'
        self.resource = resource  # ex: 'document', 'user', '*'
        
    def __eq__(self, other):
        if not isinstance(other, Permission):
            return False
        return self.action == other.action and self.resource == other.resource

    def __hash__(self):
        return hash((self.action, self.resource))

    def __repr__(self):
        return f"{self.action}:{self.resource}"


class Role:
    def __init__(self, name: str):
        self.name = name
        self.permissions: Set[Permission] = set()
        self.parents: Set['Role'] = set()  # Herança de papéis

    def add_permission(self, permission: Permission):
        self.permissions.add(permission)

    def add_parent(self, parent_role: 'Role'):
        self.parents.add(parent_role)

    def get_effective_permissions(self, visited: Optional[Set[str]] = None) -> Set[Permission]:
        if visited is None:
            visited = set()
        
        if self.name in visited:
            return set()
        
        visited.add(self.name)
        effective = set(self.permissions)
        
        for parent in self.parents:
            effective.update(parent.get_effective_permissions(visited))
            
        return effective


class User:
    def __init__(self, username: str):
        self.username = username
        self.roles: Set[Role] = set()
        self.explicit_denials: Set[Permission] = set() # Negação explícita

    def assign_role(self, role: Role):
        self.roles.add(role)

    def deny_permission(self, permission: Permission):
        self.explicit_denials.add(permission)

    def has_permission(self, action: str, resource_instance: str = "*") -> bool:
        # 1. Verifica negação explícita (ação global ou recurso específico)
        for denial in self.explicit_denials:
            if denial.action == action and (denial.resource == "*" or denial.resource == resource_instance):
                return False

        # 2. Coleta permissões de todos os papéis (incluindo hierarquia)
        effective_permissions: Set[Permission] = set()
        for role in self.roles:
            effective_permissions.update(role.get_effective_permissions())

        # 3. Valida se possui a permissão solicitada
        for perm in effective_permissions:
            if perm.action == action:
                if perm.resource == "*" or perm.resource == resource_instance:
                    return True

        return False


class RBACEngine:
    def __init__(self):
        self.roles: Dict[str, Role] = {}
        self.users: Dict[str, User] = {}

    def create_role(self, name: str) -> Role:
        role = Role(name)
        self.roles[name] = role
        return role

    def get_role(self, name: str) -> Optional[Role]:
        return self.roles.get(name)

    def create_user(self, username: str) -> User:
        user = User(username)
        self.users[username] = user
        return user

    def get_user(self, username: str) -> Optional[User]:
        return self.users.get(username)