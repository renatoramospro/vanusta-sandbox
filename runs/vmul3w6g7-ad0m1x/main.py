path=simulator.py
class DatabaseSelector:
    """
    Framework de Seleção de Persistência Poliglota.
    Mapeia padrões de acesso e requisitos não-funcionais para o motor de banco de dados ideal.
    """
    
    WORKLOADS = {
        "OLTP_ACID": {
            "best_fit": "Relacional (RDBMS)",
            "justification": "Exige transações ACID estritas e integridade referencial com joins complexos.",
            "trade_off": "Menor escalabilidade horizontal nativa em comparação ao NoSQL; maior contenção de locks sob escrita extrema."
        },
        "DOCUMENT_FLEX": {
            "best_fit": "NoSQL Document (Ex: MongoDB)",
            "justification": "Modelagem orientada a agregados com esquemas dinâmicos/aninhados sem necessidade de joins.",
            "trade_off": "Consistência eventual ou restrita ao documento; joins agregados custosos em termos de performance se normalizados em excesso."
        },
        "KEY_VALUE_CACHE": {
            "best_fit": "NoSQL Key-Value (Ex: Redis / DynamoDB)",
            "justification": "Acesso por chave primária exata O(1), altíssimo throughput e latência na casa de microssegundos.",
            "trade_off": "Falta de capacidade para consultas secundárias complexas ou agregações analíticas."
        },
        "TIME_SERIES_COLUMNS": {
            "best_fit": "NoSQL Column-Family (Ex: Cassandra / ClickHouse)",
            "justification": "Escritas massivas em append-only e leituras colunares otimizadas para alta largura de banda.",
            "trade_off": "Modelagem altamente dependente das queries de leitura (query-driven design); flexibilidade de schema limitada nas chaves de partição."
        },
        "CONNECTED_GRAPH": {
            "best_fit": "NoSQL Graph (Ex: Neo4j)",
            "justification": "Travessias profundas e recursivas de grafos (vários saltos/hops) onde Joins relacionais colapsam.",
            "trade_off": "Escalabilidade horizontal distribuída complexa e cara; consumo de memória elevado para manter índices de ponteiros."
        }
    }

    def evaluate(self, access_pattern: str, needs_acid: bool, deep_relations: bool, write_heavy: bool) -> dict:
        """
        Avalia os parâmetros da carga de trabalho e retorna o motor de banco de dados recomendado.
        """
        if deep_relations:
            key = "CONNECTED_GRAPH"
        elif write_heavy and not needs_acid:
            key = "TIME_SERIES_COLUMNS"
        elif access_pattern == "key_lookup" and not needs_acid:
            key = "KEY_VALUE_CACHE"
        elif access_pattern == "nested_json":
            key = "DOCUMENT_FLEX"
        else:
            key = "OLTP_ACID"
            
        result = self.WORKLOADS[key].copy()
        result["selected_workload"] = key
        return result

def test_selector_framework():
    selector = DatabaseSelector()
    
    # Caso 1: Sistema de Pagamentos Bancários (Transacional estrito)
    res1 = selector.evaluate(access_pattern="relational_joins", needs_acid=True, deep_relations=False, write_heavy=False)
    assert res1["best_fit"] == "Relacional (RDBMS)", f"Esperado RDBMS, obtido {res1['best_fit']}"
    
    # Caso 2: Rede Social - Amigos de amigos (Travessias profundas)
    res2 = selector.evaluate(access_pattern="graph_traversal", needs_acid=True, deep_relations=True, write_heavy=False)
    assert res2["best_fit"] == "NoSQL Graph (Ex: Neo4j)", f"Esperado Graph, obtido {res2['best_fit']}"
    
    # Caso 3: Telemetria IoT de alta frequência
    res3 = selector.evaluate(access_pattern="append_only", needs_acid=False, deep_relations=False, write_heavy=True)
    assert res3["best_fit"] == "NoSQL Column-Family (Ex: Cassandra / ClickHouse)"
    
    # Caso 4: Catálogo de Produtos com atributos flexíveis
    res4 = selector.evaluate(access_pattern="nested_json", needs_acid=False, deep_relations=False, write_heavy=False)
    assert res4["best_fit"] == "NoSQL Document (Ex: MongoDB)"
    
    # Caso 5: Sessão de usuário / Cache de alta velocidade
    res5 = selector.evaluate(access_pattern="key_lookup", needs_acid=False, deep_relations=False, write_heavy=False)
    assert res5["best_fit"] == "NoSQL Key-Value (Ex: Redis / DynamoDB)"
    
    print("Sucesso: Todas as 5 cargas de trabalho foram mapeadas corretamente pelo framework sem erros de sintaxe.")

if __name__ == "__main__":
    test_selector_framework()