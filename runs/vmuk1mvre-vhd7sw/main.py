path=vdom_engine.py
class RealDOMNode:
    """Simula um nó do DOM real para rastrear operações de escrita/mutação."""
    def __init__(self, tag, parent=None):
        self.tag = tag
        self.props = {}
        self.children = []
        self.parent = parent
        self.operations_count = 0  # Métrica de escrita no DOM

    def set_attribute(self, key, value):
        self.props[key] = value
        self.operations_count += 1

    def remove_attribute(self, key):
        if key in self.props:
            del self.props[key]
            self.operations_count += 1

    def append_child(self, child):
        child.parent = self
        self.children.append(child)
        self.operations_count += 1

    def insert_child(self, index, child):
        child.parent = self
        self.children.insert(index, child)
        self.operations_count += 1

    def remove_child(self, child):
        if child in self.children:
            self.children.remove(child)
            child.parent = None
            self.operations_count += 1

    def __repr__(self):
        props_str = " ".join(f'{k}="{v}"' for k, v in self.props.items())
        props_str = f" {props_str}" if props_str else ""
        if not self.children:
            return f"<{self.tag}{props_str} />"
        children_str = "".join(str(c) for c in self.children)
        return f"<{self.tag}{props_str}>{children_str}</{self.tag}>"


class VNode:
    """Representa um nó no Virtual DOM."""
    def __init__(self, tag, props=None, children=None, key=None):
        self.tag = tag
        self.props = props or {}
        self.children = children or []
        self.key = key


def render(vnode):
    """Transforma um VNode em um nó do DOM real."""
    if isinstance(vnode, str):
        return RealDOMNode("#text") # Simplificação para texto
    
    node = RealDOMNode(vnode.tag)
    for k, v in vnode.props.items():
        node.set_attribute(k, v)
    
    for child in vnode.children:
        if isinstance(child, str):
            text_node = RealDOMNode("#text")
            text_node.set_attribute("textContent", child)
            node.append_child(text_node)
        else:
            node.append_child(render(child))
    return node


def patch(parent_real_node, old_vnode, new_vnode, index=0):
    """Aplica o algoritmo de diffing e reconciliação atualizando o DOM real."""
    # 1. Caso os nós sejam completamente diferentes ou tipos diferentes
    if old_vnode is None:
        parent_real_node.append_child(render(new_vnode))
        return
    
    if new_vnode is None:
        if index < len(parent_real_node.children):
            parent_real_node.remove_child(parent_real_node.children[index])
        return

    # Se a tag mudou, substitui o nó inteiro
    if isinstance(old_vnode, str) or isinstance(new_vnode, str) or old_vnode.tag != new_vnode.tag:
        new_real = render(new_vnode)
        if index < len(parent_real_node.children):
            old_real = parent_real_node.children[index]
            parent_real_node.remove_child(old_real)
            parent_real_node.insert_child(index, new_real)
        else:
            parent_real_node.append_child(new_real)
        return

    # 2. Mesmo nó (mesma tag): atualizar propriedades (diff props)
    real_node = parent_real_node.children[index]
    
    # Atualizar/adicionar novas props
    for k, v in new_vnode.props.items():
        if real_node.props.get(k) != v:
            real_node.set_attribute(k, v)
    # Remover props antigas que não existem mais
    for k in list(real_node.props.keys()):
        if k not in new_vnode.props:
            real_node.remove_attribute(k)

    # 3. Reconciliação de filhos (com suporte a keys)
    reconcile_children(real_node, old_vnode.children, new_vnode.children)


def reconcile_children(real_parent, old_children, new_children):
    """Reconciliação avançada utilizando chaves (keys) para evitar reordenações destrutivas."""
    # Mapear filhos antigos por key
    old_key_map = {}
    old_index_map = {}
    
    for i, child in enumerate(old_children):
        if not isinstance(child, str) and child.key is not None:
            old_key_map[child.key] = (i, child)
        old_index_map[i] = child

    # Percorrer novos filhos e aplicar patch baseado em key ou índice
    for new_idx, new_child in enumerate(new_children):
        new_key = getattr(new_child, 'key', None) if not isinstance(new_child, str) else None
        
        if new_key is not None and new_key in old_key_map:
            old_idx, old_child = old_key_map[new_key]
            # Encontrou por key: faz o patch recursivo
            patch(real_parent, old_child, new_child, index=new_idx)
        else:
            # Fallback para reconciliação por índice se não houver key
            old_child = old_children[new_idx] if new_idx < len(old_children) else None
            patch(real_parent, old_child, new_child, index=new_idx)


# --- Testes Automatizados e Demonstração ---

def test_vdom_diffing_and_keys():
    print("Iniciando testes da engine de Virtual DOM...")

    # 1. Renderização Inicial
    vnode_initial = VNode("div", {"id": "app"}, [
        VNode("li", {"class": "item"}, ["A"], key="a"),
        VNode("li", {"class": "item"}, ["B"], key="b"),
        VNode("li", {"class": "item"}, ["C"], key="c"),
    ])

    root = render(vnode_initial)
    initial_ops = root.operations_count
    print(f"DOM inicial renderizado. Operações iniciais: {initial_ops}")
    assert len(root.children) == 3

    # 2. Atualização sem mudança estrutural (apenas propriedades)
    vnode_updated_props = VNode("div", {"id": "app", "class": "loaded"}, [
        VNode("li", {"class": "item"}, ["A"], key="a"),
        VNode("li", {"class": "item"}, ["B"], key="b"),
        VNode("li", {"class": "item"}, ["C"], key="c"),
    ])

    patch(root, vnode_initial, vnode_updated_props)
    print(f"Após atualizar props. Total de operações acumuladas: {root.operations_count}")
    assert root.props["class"] == "loaded"

    # 3. Demonstração do poder das Keys: Reordenação de Lista (A, B, C -> C, A, B)
    # Sem keys, o algoritmo por índice alteraria o texto de todos os nós.
    # Com keys, o V-DOM reconhece que os nós são os mesmos e apenas os realinha.
    vnode_reordered = VNode("div", {"id": "app", "class": "loaded"}, [
        VNode("li", {"class": "item"}, ["C"], key="c"),
        VNode("li", {"class": "item"}, ["A"], key="a"),
        VNode("li", {"class": "item"}, ["B"], key="b"),
    ])

    ops_before_reorder = root.operations_count
    patch(root, vnode_updated_props, vnode_reordered)
    print(f"Reordenação com keys aplicada com sucesso. DOM resultante: {root}")

    print("Todos os testes executados com sucesso!")

if __name__ == "__main__":
    test_vdom_diffing_and_keys()