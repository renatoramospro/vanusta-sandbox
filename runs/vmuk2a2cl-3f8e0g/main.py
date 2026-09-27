class RealDOMNode:
    """Simula um nó do DOM real para rastrear operações de escrita/mutação."""
    def __init__(self, tag, parent=None, text=None):
        self.tag = tag
        self.props = {}
        self.children = []
        self.parent = parent
        self.text = text
        self.operations_count = 0  # Métrica de escrita no DOM real

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

    def remove_child(self, index):
        if 0 <= index < len(self.children):
            child = self.children.pop(index)
            child.parent = None
            self.operations_count += 1
            return child
        return None

    def __repr__(self):
        if self.tag == "#text":
            return self.text
        props_str = "".join(f' {k}="{v}"' for k, v in self.props.items())
        children_str = "".join(str(c) for c in self.children)
        return f"<{self.tag}{props_str}>{children_str}</{self.tag}>"


class VNode:
    """Representa um nó no Virtual DOM."""
    def __init__(self, tag, props=None, children=None, key=None):
        self.tag = tag
        self.props = props or {}
        self.children = children or []
        self.key = key

    def __repr__(self):
        return f"VNode(tag={self.tag}, key={self.key}, props={self.props}, children={self.children})"


def render(vnode):
    """Converte um VNode em um RealDOMNode recursivamente."""
    if isinstance(vnode, str):
        return RealDOMNode("#text", text=vnode)
    
    node = RealDOMNode(vnode.tag)
    for k, v in vnode.props.items():
        node.set_attribute(k, v)
    
    for child in vnode.children:
        real_child = render(child)
        node.append_child(real_child)
        
    return node


def patch_props(real_node, old_props, new_props):
    """Atualiza propriedades de um nó real com base no diff."""
    for key, new_val in new_props.items():
        old_val = old_props.get(key)
        if old_val != new_val:
            real_node.set_attribute(key, new_val)
    
    for key in old_props:
        if key not in new_props:
            real_node.remove_attribute(key)


def patch(real_node, old_vnode, new_vnode):
    """Aplica o algoritmo de diffing e reconciliação (com suporte a keys)."""
    if old_vnode is new_vnode:
        return real_node

    # Se a tag ou tipo mudou completamente, substitui o nó inteiro
    if type(old_vnode) != type(new_vnode) or (isinstance(old_vnode, VNode) and old_vnode.tag != new_vnode.tag):
        if real_node.parent:
            idx = real_node.parent.children.index(real_node)
            new_real = render(new_vnode)
            real_node.parent.remove_child(idx)
            real_node.parent.insert_child(idx, new_real)
            return new_real
        return render(new_vnode)

    # Se for texto puro
    if isinstance(new_vnode, str):
        if old_vnode != new_vnode:
            real_node.text = new_vnode
            real_node.operations_count += 1
        return real_node

    # Atualiza propriedades do elemento
    patch_props(real_node, old_vnode.props, new_vnode.props)

    # Reconciliação de filhos utilizando keys (Keyed Diffing)
    old_children = old_vnode.children
    new_children = new_vnode.children

    # Mapeia keys antigas para seus nós reais e índices
    old_key_map = {}
    for idx, child in enumerate(old_children):
        if isinstance(child, VNode) and child.key is not None:
            old_key_map[child.key] = (idx, child, real_node.children[idx])

    # Reconciliação passo a passo
    new_real_children = []
    
    for new_idx, new_child in enumerate(new_children):
        new_key = getattr(new_child, 'key', None)
        
        if new_key is not None and new_key in old_key_map:
            old_idx, matched_vnode, matched_real = old_key_map[new_key]
            # Recursão para atualizar o nó existente
            patch(matched_real, matched_vnode, new_child)
            
            # Reordena no DOM real se necessário
            current_pos = real_node.children.index(matched_real)
            if current_pos != new_idx:
                real_node.children.pop(current_pos)
                real_node.insert_child(new_idx, matched_real)
            else:
                new_real_children.append(matched_real)
        else:
            # Novo nó ou sem key
            if new_idx < len(real_node.children):
                # Tenta atualizar no lugar se houver correspondência posicional
                existing_real = real_node.children[new_idx]
                existing_vnode = old_children[new_idx] if new_idx < len(old_children) else None
                if existing_vnode and not getattr(new_child, 'key', None) and not getattr(existing_vnode, 'key', None):
                    patch(existing_real, existing_vnode, new_child)
                    new_real_children.append(existing_real)
                else:
                    new_real = render(new_child)
                    real_node.insert_child(new_idx, new_real)
                    new_real_children.append(new_real)
            else:
                new_real = render(new_child)
                real_node.append_child(new_real)
                new_real_children.append(new_real)

    # Remove nós excedentes antigos
    while len(real_node.children) > len(new_children):
        real_node.remove_child(len(real_node.children) - 1)

    return real_node


def test_vdom_diffing_and_keys():
    print("Iniciando testes da Engine de Virtual DOM...")

    # 1. Renderização Inicial
    vnode_initial = VNode("div", {"id": "app", "class": "init"}, [
        VNode("li", {"class": "item"}, ["A"], key="a"),
        VNode("li", {"class": "item"}, ["B"], key="b"),
        VNode("li", {"class": "item"}, ["C"], key="c"),
    ])

    root = render(vnode_initial)
    initial_ops = root.operations_count
    print(f"DOM inicial renderizado. Operações iniciais: {initial_ops}")
    assert len(root.children) == 3

    # 2. Atualização de propriedades sem mudança estrutural
    vnode_updated_props = VNode("div", {"id": "app", "class": "loaded"}, [
        VNode("li", {"class": "item"}, ["A"], key="a"),
        VNode("li", {"class": "item"}, ["B"], key="b"),
        VNode("li", {"class": "item"}, ["C"], key="c"),
    ])

    patch(root, vnode_initial, vnode_updated_props)
    print(f"Após atualizar props. Total de operações acumuladas: {root.operations_count}")
    assert root.props["class"] == "loaded"

    # 3. Reordenação com keys (A, B, C -> C, A, B)
    vnode_reordered = VNode("div", {"id": "app", "class": "loaded"}, [
        VNode("li", {"class": "item"}, ["C"], key="c"),
        VNode("li", {"class": "item"}, ["A"], key="a"),
        VNode("li", {"class": "item"}, ["B"], key="b"),
    ])

    patch(root, vnode_updated_props, vnode_reordered)
    print(f"Reordenação com keys aplicada com sucesso. DOM resultante: {root}")
    
    # Asserções corrigidas validando o nó de texto estruturado corretamente
    assert root.children[0].children[0].text == "C"
    assert root.children[1].children[0].text == "A"
    assert root.children[2].children[0].text == "B"

    print("Todos os testes executados com sucesso!")

if __name__ == "__main__":
    test_vdom_diffing_and_keys()