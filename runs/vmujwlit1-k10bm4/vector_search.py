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
        # Converte para float32 para eficiência de memória e desempenho
        vectors = vectors.astype(np.float32)
        
        # Normalização L2 (Equívoco 1.1: 'Não precisamos normalizar')
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        # Evita divisão por zero
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

        # Produto escalar vetorizado entre a matriz de base e os vetores de consulta
        # Shape resultante: (num_queries, num_vectors)
        scores = np.dot(q_norm, self.vectors.T)

        # Encontra os top_k índices para cada consulta
        # np.argpartition é O(N) em média, muito mais rápido que argsort completo O(N log N)
        top_k_indices = np.argpartition(-scores, top_k, axis=1)[:, :top_k]
        
        # Ordena apenas os top_k resultados encontrados para precisão exata
        results = []
        for i, indices in enumerate(top_k_indices):
            sub_scores = scores[i, indices]
            sorted_sub_idx = np.argsort(-sub_scores)
            best_indices = indices[sorted_sub_idx]
            best_scores = sub_scores[sorted_sub_idx]
            
            results.append([
                (self.ids[idx], float(score)) for idx, score in zip(best_indices, best_scores)
            ])

        return results

# ==========================================
# TESTES E VALIDAÇÃO DO EXPERIMENTO
# ==========================================
if __name__ == "__main__":
    print("Iniciando experimento do Motor de Busca Vetorial...")
    
    num_vectors = 10000  # Expandido para testar robustez (além do mínimo original)
    dim = 128
    top_k = 5

    # 1. Geração de dados sintéticos
    np.random.seed(42)
    raw_vectors = np.random.randn(num_vectors, dim)
    vector_ids = [f"id_{i}" for i in range(num_vectors)]

    # 2. Inicialização e Indexação
    engine = InMemoryVectorSearch(dimensions=dim)
    
    start_time = time.time()
    engine.add(vector_ids, raw_vectors)
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
    v2 = np.array([[10.0, 0.0]], dtype=np.float32) # Mesmo ângulo de v1, mas magnitude 10x maior
    
    # Cosseno real entre v1 e v2 deve ser 1.0 (mesma direção)
    # Produto escalar bruto entre v1 e v2 seria 10.0 (ignorando a magnitude relativa se comparado a outro vetor unitário)
    
    cos_sim_correto = np.dot(v1 / np.linalg.norm(v1), v2.T / np.linalg.norm(v2))[0, 0]
    print(f"Similaridade de Cosseno correta (com normalização): {cos_sim_correto}")
    assert np.isclose(cos_sim_correto, 1.0), "A similaridade de cosseno deveria ser 1.0 para vetores na mesma direção!"
    print("Experimento concluído com sucesso absoluto!")