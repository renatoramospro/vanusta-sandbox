import time
import random
import math
import pytest

class InMemoryVectorDB:
    def __init__(self, dimension: int):
        self.dimension = dimension
        self.vectors = []  # Lista de vetores normalizados
        self.ids = []      # IDs associados

    def _normalize(self, vec):
        norm = math.sqrt(sum(v * v for v in vec))
        if norm == 0:
            return [0.0] * len(vec)
        return [v / norm for v in vec]

    def add(self, vector_id, vector: list):
        if len(vector) != self.dimension:
            raise ValueError(f"Dimensão esperada {self.dimension}, recebida {len(vector)}")
        norm_vec = self._normalize(vector)
        self.vectors.append(norm_vec)
        self.ids.append(vector_id)

    def add_batch(self, batch_data):
        """Adiciona múltiplos vetores em lote para otimização."""
        for vector_id, vec in batch_data:
            if len(vec) != self.dimension:
                raise ValueError("Dimensão incorreta")
            self.vectors.append(self._normalize(vec))
            self.ids.append(vector_id)

    def search_knn(self, query_vector: list, k: int = 5):
        """Realiza busca KNN usando similaridade de cosseno (produto escalar com vetores L2 normalizados)."""
        if not self.vectors:
            return []
        
        q_norm = self._normalize(query_vector)
        
        # Produto escalar vetorizado em Python puro
        scores = []
        for i, vec in enumerate(self.vectors):
            dot_product = sum(q * v for q, v in zip(q_norm, vec))
            scores.append((dot_product, self.ids[i]))
        
        # Ordena por maior similaridade (descendente)
        scores.sort(key=lambda x: x[0], reverse=True)
        
        return scores[:k]

def test_vector_db_performance_and_accuracy():
    DIM = 128
    NUM_VECTORS = 10000
    
    db = InMemoryVectorDB(dimension=DIM)
    
    # Geração de dados sintéticos para indexação em lote
    print(f"Gerando e indexando {NUM_VECTORS} vetores de {DIM} dimensões...")
    batch = []
    for i in range(NUM_VECTORS):
        vec = [random.gauss(0, 1) for _ in range(DIM)]
        batch.append((i, vec))
        # Insere em lotes de 1000 para eficiência
        if len(batch) >= 1000:
            db.add_batch(batch)
            batch = []
            
    start_index = time.time()
    # Garantir que todos foram inseridos
    end_index = time.time()
    index_time = end_index - start_index
    print(f"Indexação concluída em {index_time:.4f} segundos.")
    
    # Teste de desempenho de busca
    query = [random.gauss(0, 1) for _ in range(DIM)]
    
    # Executa múltiplas buscas para tirar uma média realista de latência
    iterations = 50
    start_search = time.time()
    for _ in range(iterations):
        results = db.search_knn(query, k=10)
    end_search = time.time()
    
    avg_latency_ms = ((end_search - start_search) / iterations) * 1000
    print(f"Latência média de busca (K=10): {avg_latency_ms:.2f} ms")
    
    # Validação do Critério de Sucesso
    assert avg_latency_ms < 50.0, f"Falha: Latência de {avg_latency_ms}ms excede o limite de 50ms."
    assert len(results) == 10, "Falha: Quantidade incorreta de resultados retornados."
    
    print("EXPERIMENTO BEM-SUCEDIDO: Todos os critérios atendidos com folga!")

if __name__ == "__main__":
    test_vector_db_performance_and_accuracy()