import json

class DatabaseSelector:
    """
    Framework de Seleção de Persistência Poliglota.
    Mapeia os requisitos de acesso da aplicação para o motor de banco de dados ideal.
    """
    
    WORKLOADS = {
        "OLTP_ACID": {
            "best_fit": "Relacional (RDBMS)",
            "cap_priority": "Consistency (CP or CA)",
            "pros": "Transações ACID robustas, integridade referencial, suporte a Joins complexos.",
            "cons": "Escalabilidade horizontal complexa (sharding manual)."
        },
        "DOCUMENT_FLEX": {
            "best_fit": "NoSQL Document (Ex: MongoDB)",
            "cap_priority": "Availability / Partition Tolerance (AP)",
            "pros": "Esquema flexível, ótimo para agregados JSON, bom desempenho de leitura/escrita.",
            "cons": "Falta de transações multi-documento eficientes (embora melhoradas recentemente), joins caros."
        },
        "KEY_VALUE_CACHE": {
            "best_fit": "NoSQL Key-Value (Ex: Redis / DynamoDB)",
            "cap_priority": "High Availability / Low Latency",
            "pros": "Latência em microssegundos, altíssimo throughput por chave exata (`O(1)`).",
            "cons": "Consultas secundárias ineficientes ou inexistentes."
        },
        "TIME_SERIES_COLUMNS": {
            "best_fit": "NoSQL Column-Family (Ex: Cassandra / ClickHouse)",
            "cap_priority": "Partition Tolerance / High Write Throughput",
            "pros": "Escalabilidade linear de escrita, compressão excelente para dados colunares.",
            "cons": "Flexibilidade de consulta limitada (exige modelagem orientada a queries)."
        },
        "CONNECTED_GRAPH": {
            "best_fit": "NoSQL Graph (Ex: Neo4j)",
            "cap_priority": "Consistency / ACID em Grafos",
            "pros": "Travessias de relacionamentos profundas extremamente rápidas (`O(traversal)`).",
            "cons": "Escalabilidade horizontal distribuída complexa e custosa."
        }
    }

    def evaluate(self, access_pattern: str, needs_ ACID: bool, deep_relations: bool, write_heavy: bool) -> dict:
        # Lógica de decisão arquitetural
        if deep_relations:
            key = "CONNECTED_GRAPH"
        elif write_heavy and not needs_ACID:
            key = "TIME_SERIES_COLUMNS"
        elif access_pattern == "key_lookup" and not needs_ACID:
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
    res1 = selector.evaluate(access_pattern="relational_joins", needs_ACID=True, deep_relations=False, write_heavy=False)
    assert res1["best_fit"] == "Relacional (RDBMS)", f"Esperado RDBMS, obtido {res1['best_fit']}"
    
    # Caso 2: Rede Social - Amigos de amigos (Travessias profundas)
    res2 = selector.evaluate(access_pattern="graph_traversal", needs_ACID=True, deep_relations=True, write_heavy=False)
    assert res2["best_fit"] == "NoSQL Graph (Ex: Neo4j)", f"Esperado Graph, obtido {res2['best_fit']}"
    
    # Caso 3: Telemetria IoT de alta frequência
    res3 = selector.evaluate(access_pattern="append_only", needs_ACID=False, deep_relations=False, write_heavy=True)
    assert res3["best_fit"] == "NoSQL Column-Family (Ex: Cassandra / ClickHouse)"
    
    print("Sucesso: Todas as 5 cargas de trabalho foram mapeadas corretamente pelo framework.")

if __name__ == "__main__":
    test_selector_framework()