class RealDOMNode:
    """Simula um nó do DOM real para rastrear operações de escrita/mutação."""
    def __init__(self, tag, parent=None):
        self.tag = tag
        self.props = {}
        self.children = []
        self.parent = parent
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

    def remove_child(self, child):
        if child in self.children:
            self.children.remove(child)
            child.parent = None
            self.operations_count += 1

    def update_text(self, text):
        self.text = text
        self.operations_count += 1

    def __repr__(self):
        props_str = " ".join(f'{k}="{v}"' for k, v in self.props.items())
        props_str = f" {props_str}" if props_str else ""
        if hasattr(self, 'text'):
            return f"<{self.tag}{props_str}>{self.text}</{self.tag}>"
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
        children_str = ", ".join(str(c) for c in self.children)
        return f"VNode(tag={self.tag!r}, props={self.props!r}, children=[{children_str}], key={self.key!r})"


def render(vnode):
    """Transforma um VNode em um nó do DOM real recursivamente."""
    if isinstance(vnode, str):
        node = RealDOMNode("#text")
        node.text = vnode
        node.operations_count += 1
        return node

    dom_node = RealDOMNode(vnode.tag)
    for k, v in vnode.props.items():
        dom_node.set_attribute(k, v)

    for child in vnode.children:
        child_dom = render(child)
        dom_node.append_child(child_dom)

    return dom_node


def patch(dom_node, old_vnode, new_vnode):
    """Aplica o algoritmo de diffing e reconciliação atualizando o DOM real estritamente necessário."""
    # 1. Se o tipo do nó (tag) mudou, substitui a subárvore inteira
    if isinstance(old_vnode, str) or isinstance(new_vnode, str) or old_vnode.tag != new_vnode.tag:
        if dom_node.parent is not None:
            new_dom = render(new_vnode)
            idx = dom_node.parent.children.index(dom_node)
            dom_node.parent.remove_child(dom_node)
            dom_node.parent.insert_child(idx, new_dom)
        return

    # 2. Atualização de Propriedades
    for k, v in new_vnode.props.items():
        if dom_node.props.get(k) != v:
            dom_node.set_attribute(k, v)
    for k in list(dom_node.props.keys()):
        if k not in new_vnode.props:
            dom_node.remove_attribute(k)

    # 3. Tratamento de nó de texto puro
    if len(new_vnode.children) == 1 and isinstance(new_vnode.children[0], str):
        if not hasattr(dom_node, 'text') or dom_node.text != new_vnode.children[0]:
            dom_node.update_text(new_vnode.children[0])
            # Remove filhos antigos se existirem
            for child in list(dom_node.children):
                dom_node.remove_child(child)
        return

    # 4. Reconciliação de Nós Filhos com suporte a Keys
    old_children = old_vnode.children
    new_children = new_vnode.children

    # Mapeia keys antigas para reutilização eficiente
    keyed_old = {c.key: (i, c, dom_node.children[i]) for i, c in enumerate(old_children) if c.key is not None}
    
    # Abordagem simplificada de reconciliação para demonstração robusta
    # Percorre o novo array de filhos
    for i, new_child in enumerate(new_children):
        if i < len(dom_node.children):
            # Se possui key e existe mapeamento correspondente
            if isinstance(new_child, VNode) and new_child.key is not None and new_child.key in keyed_old:
                old_idx, old_v, old_dom = keyed_old[new_child.key]
                if old_dom in dom_node.children:
                    dom_node.children.remove(old_dom)
                dom_node.insert_child(i, old_dom)
                patch(old_dom, old_v, new_child)
            else:
                patch(dom_node.children[i], old_children[i], new_child)
        else:
            # Inserção de novo filho
            new_dom_child = render(new_child)
            dom_node.append_child(new_dom_child)

    # Remove excedentes
    while len(dom_node.children) > len(new_children):
        dom_node.remove_child(dom_node.children[-1])


def test_vdom_diffing_and_keys():
    print("Iniciando testes da Engine de Virtual DOM...")

    # 1. Renderização Inicial
    vnode_initial = VNode("div", {"id": "app", "class": "initial"}, [
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
    assert root.children[0].children[0].text == "C"
    assert root.children[1].children[0].text == "A"
    assert root.children[2].children[0].text == "B"

    print("Todos os testes executados com sucesso!")

if __name__ == "__main__":
    test_vdom_diffing_and_keys()