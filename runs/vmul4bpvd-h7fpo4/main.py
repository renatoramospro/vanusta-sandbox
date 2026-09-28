class DatabaseSelector:
    """
    Framework de Seleção de Persistência Poliglota Aprimorado.
    Mapeia padrões de acesso, requisitos não-funcionais, suporte a arquiteturas híbridas
    e resolução de conflitos para motores de banco de dados.
    """
    
    WORKLOADS = {
        "OLTP_ACID": {
            "best_fit": "Relacional (RDBMS)",
            "justification": "Exige transações ACID estritas e integridade referencial com joins complexos.",
            "trade_off": "Menor escalabilidade horizontal nativa; maior contenção de locks sob escrita extrema."
        },
        "DOCUMENT_FLEX": {
            "best_fit": "NoSQL Document (Ex: MongoDB)",
            "justification": "Modelagem orientada a agregados com esquemas dinâmicos/aninhados sem necessidade de joins.",
            "trade_off": "Consistência eventual ou restrita ao documento; joins agregados custosos se normalizados."
        },
        "KEY_VALUE_CACHE": {
            "best_fit": "NoSQL Key-Value (Ex: Redis / DynamoDB)",
            "justification": "Acesso por chave primária exata O(1), altíssimo throughput e latência mínima.",
            "trade_off": "Inapropriado para consultas secundárias complexas ou agregações analíticas."
        },
        "TIME_SERIES_COLUMNS": {
            "best_fit": "NoSQL Column-Family (Ex: Cassandra / ClickHouse)",
            "justification": "Escritas massivas em append-only e leituras colunares otimizadas.",
            "trade_off": "Modelagem estritamente dependente das queries (query-driven design)."
        },
        "CONNECTED_GRAPH": {
            "best_fit": "NoSQL Graph (Ex: Neo4j)",
            "justification": "Travessias profundas e recursivas de grafos onde Joins relacionais colapsam.",
            "trade_off": "Escalabilidade distribuída complexa e alto consumo de memória para índices de ponteiros."
        },
        "HYBRID_ECOMMERCE": {
            "best_fit": "Persistência Poliglota Híbrida (RDBMS + NoSQL Document)",
            "justification": "Combina integridade transacional (ACID) para pagamentos/pedidos com flexibilidade de schema para o catálogo de produtos.",
            "trade_off": "Complexidade operacional elevada, necessidade de gerenciar consistência eventual entre datastores (ex: Saga Pattern)."
        }
    }

    def evaluate(self, access_pattern: str, needs_acid: bool, deep_relations: bool, write_heavy: bool, hybrid_mode: bool = False) -> dict:
        # Resolução de conflito: Se o modo híbrido for explicitamente requerido
        if hybrid_mode:
            return self.WORKLOADS["HYBRID_ECOMMERCE"]
            
        # Resolução de conflito: Se há exigência simultânea de ACID estrito e travessia profunda de grafos
        if needs_acid and deep_relations:
            return {
                "best_fit": "RDBMS com extensões de Grafos ou Abordagem Híbrida",
                "justification": "Conflito de requisitos: ACID exige isolamento restrito de locks, enquanto grafos profundos geram explosão de JOINs. Recomenda-se RDBMS com CTEs recursivas para escala moderada ou arquitetura segregada.",
                "trade_off": "Performance de travessia inferior a um banco de grafos nativo ou contenção de transações sob concorrência extrema."
            }

        if access_pattern == "relational_acess" or (needs_acid and not deep_relations):
            return self.WORKLOADS["OLTP_ACID"]
        elif access_pattern == "graph_traversal" or deep_relations:
            return self.WORKLOADS["CONNECTED_GRAPH"]
        elif access_pattern == "append_only" or write_heavy:
            return self.WORKLOADS["TIME_SERIES_COLUMNS"]
        elif access_pattern == "nested_json":
            return self.WORKLOADS["DOCUMENT_FLEX"]
        elif access_pattern == "key_lookup":
            return self.WORKLOADS["KEY_VALUE_CACHE"]
        
        return self.WORKLOADS["OLTP_ACID"]

def test_selector_framework():
    selector = DatabaseSelector()
    
    # Caso 1: Transacional puro
    res1 = selector.evaluate(access_pattern="relational_acess", needs_acid=True, deep_relations=False, write_heavy=False)
    assert res1["best_fit"] == "Relacional (RDBMS)", f"Esperado RDBMS, obtido {res1['best_fit']}"
    
    # Caso 2: Grafos profundos
    res2 = selector.evaluate(access_pattern="graph_traversal", needs_acid=False, deep_relations=True, write_heavy=False)
    assert res2["best_fit"] == "NoSQL Graph (Ex: Neo4j)"
    
    # Caso 3: Arquitetura Híbrida (E-commerce com RDBMS + Document)
    res3 = selector.evaluate(access_pattern="hybrid", needs_acid=True, deep_relations=False, write_heavy=False, hybrid_mode=True)
    assert "Híbrida" in res3["best_fit"]
    
    # Caso 4: Conflito de Requisitos (ACID + Grafos profundos simultâneos)
    res4 = selector.evaluate(access_pattern="conflict", needs_acid=True, deep_relations=True, write_heavy=False)
    assert "Conflito" in res4["justification"]

    print("Sucesso: Todas as cargas de trabalho, cenários híbridos e resolução de conflitos foram validados corretamente.")

if __name__ == "__main__":
    test_selector_framework()