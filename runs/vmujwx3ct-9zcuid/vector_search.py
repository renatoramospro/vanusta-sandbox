import time
import numpy as np

class InMemoryVectorSearch:
    def __init__(self, dimensions: int):
        self.dimensions = dimensions
        self.vectors = None
        self.ids = []

    def add(self, ids: list, vectors: np.ndarray):
        """
        Adiciona vetores ao motor e os normaliza L2 para que 
        a similaridade de cosseno seja equivalente ao produto escalar.
        """
        vectors = vectors.astype(np.float32)
        
        # Normalização L2 (Garante que a magnitude seja 1.0)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0.0] = 1.0
        normalized_vectors = vectors / norms

        if self.vectors is None:
            self.vectors = normalized_vectors
        else:
            self.vectors = np.vstack([self.vectors, normalized_vectors])
        
        self.ids.extend(ids)

    def search(self, query_vectors: np.ndarray, top_k: int = 5):
        """
        Realiza busca por vizinhos mais próximos usando produto escalar 
        sobre vetores normalizados (Similaridade de Cosseno).
        """
        query_vectors = query_vectors.astype(np.float32)
        
        # Normaliza também os vetores de consulta
        norms = np.linalg.norm(query_vectors, axis=1, keepdims=True)
        norms[norms == 0.0] = 1.0
        q_norm = query_vectors / norms

        # Produto escalar vetorizado entre a base e os vetores de consulta
        scores = np.dot(q_norm, self.vectors.T)

        # Encontra os top_k índices para cada consulta usando argpartition para eficiência O(N)
        top_k_indices = np.argpartition(-scores, top_k, axis=1)[:, :top_k]
        
        results = []
        for i, q_indices in enumerate(top_k_indices):
            # Ordena os top_k encontrados em ordem decrescente de similaridade
            sorted_sub_indices = q_indices[np.argsort(-scores[i, q_indices])]
            q_results = [(self.ids[idx], float(scores[i, idx])) for idx in sorted_sub_indices]
            results.append(q_results)

        return results

if __name__ == "__main__":
    print("Iniciando teste do motor de busca vetorial com NumPy...")
    
    dim = 128
    num_vectors = 1000
    top_k = 5

    engine = InMemoryVectorSearch(dimensions=dim)

    # 1. Geração de dados sintéticos
    np.random.seed(42)
    sample_vectors = np.random.randn(num_vectors, dim)
    sample_ids = [f"id_{i}" for i in range(num_vectors)]

    # 2. Indexação
    start_time = time.time()
    engine.add(sample_ids, sample_vectors)
    index_time = time.time() - start_time
    print(f"[Sucesso] Indexados {num_vectors} vetores de {dim} dimensões em {index_time:.4f}s")

    # 3. Execução da Consulta
    num_queries = 10
    query_vectors = np.random.randn(num_queries, dim)

    start_time = time.time()
    results = engine.search(query_vectors, top_k=top_k)
    query_time = time.time() - start_time

    print(f"[Sucesso] Realizadas {num_queries} consultas (top-{top_k}) em {query_time * 1000:.4f} ms")
    print(f"Tempo médio por consulta: {(query_time / num_queries) * 1000:.4f} ms")

    # Validação do critério de sucesso (latência < 10ms por lote/consulta)
    assert (query_time / num_queries) * 1000 < 10.0, "Latência excedeu o limite de 10ms!"

    # 4. Demonstração do Contraexemplo (Equívoco Comum: Não normalizar)
    print("\n[Contraexemplo] Testando o impacto de NÃO normalizar os vetores...")
    v1 = np.array([[1.0, 0.0]], dtype=np.float32)
    v2 = np.array([[10.0, 0.0]], dtype=np.float32) # Mesmo ângulo, magnitude 10x maior
    
    cos_sim_correto = np.dot(v1 / np.linalg.norm(v1), v2.T / np.linalg.norm(v2))[0, 0]
    print(f"Similaridade de Cosseno correta (com normalização): {cos_sim_correto}")
    assert np.isclose(cos_sim_correto, 1.0), "A similaridade de cosseno deveria ser 1.0 para vetores na mesma direção!"
    print("Experimento concluído com sucesso absoluto!")