import time
import random
import re
from collections import defaultdict

# --- 1. Pré-processamento e Shingling ---
def tokenize_and_shingle(text, k=3):
    """Normaliza o texto, remove pontuação e extrai k-shingles (caracteres ou palavras)."""
    # Normalização básica: lowercase e remoção de caracteres não alfanuméricos excessivos
    text = re.sub(r'\s+', ' ', text.lower()).strip()
    words = text.split()
    if len(words) < k:
        # Se for menor que k palavras, usa a própria frase ou padding
        return {text}
    
    shingles = set()
    for i in range(len(words) - k + 1):
        shingle = " ".join(words[i:i+k])
        shingles.add(shingle)
    return shingles

def jaccard_similarity(set1, set2):
    """Calcula a similaridade de Jaccard exata entre dois conjuntos."""
    if not set1 and not set2:
        return 1.0
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union > 0 else 0.0

# --- 2. MinHash Implementation ---
class MinHash:
    def __init__(self, num_hashes=100):
        self.num_hashes = num_hashes
        # Parâmetros para funções de hash lineares universais: h(x) = (a * x + b) % c
        # Usando um primo grande para o espaço de hash
        self.prime = 4294967311 # Primo de 32-bit grande
        random.seed(42) # Reprodutibilidade
        self.hash_params = [
            (random.randint(1, self.prime - 1), random.randint(0, self.prime - 1))
            for _ in range(num_hashes)
        ]

    def _hash_str(self, s, a, b):
        # Converte string para inteiro via hash embutido do python misturado com parâmetros
        val = hash(s) & 0xffffffff
        return (a * val + b) % self.prime

    def compute_signature(self, shingles):
        """Gera a assinatura MinHash (vetor de inteiros) para um conjunto de shingles."""
        signature = []
        for a, b in self.hash_params:
            min_val = float('inf')
            for shingle in shingles:
                h_val = self._hash_str(shingle, a, b)
                if h_val < min_val:
                    min_val = h_val
            signature.append(min_val)
        return signature

# --- 3. LSH (Locality-Sensitive Hashing) Implementation ---
class LSH:
    def __init__(self, num_hashes=100, bands=20):
        self.num_hashes = num_hashes
        self.bands = bands
        assert num_hashes % bands == 0, "num_hashes deve ser divisível por bands"
        self.rows_per_band = num_hashes // bands
        # Múltiplas hash tables, uma para cada banda
        self.buckets = [defaultdict(list) for _ in range(bands)]

    def insert(self, doc_id, signature):
        """Insere a assinatura de um documento nas tabelas hash das bandas."""
        for b_idx in range(self.bands]:
            start = b_idx * self.rows_per_band
            end = start + self.rows_per_band
            # A chave do bucket é a tupla da faixa da assinatura nessa banda
            band_slice = tuple(signature[start:end])
            self.buckets[b_idx][band_slice].append(doc_id)

    def query(self, signature):
        """Retorna candidatos a documentos similares usando as bandas LSH."""
        candidates = set()
        for b_idx in range(self.bands):
            start = b_idx * self.rows_per_band
            end = start + self.rows_per_band
            band_slice = tuple(signature[start:end])
            if band_slice in self.buckets[b_idx]:
                for doc_id in self.buckets[b_idx][band_slice]:
                    candidates.add(doc_id)
        return candidates

# --- 4. Experimento e Validação ---
def run_experiment():
    print("Iniciando experimento de MinHash + LSH...")
    
    # Geração de corpus sintético
    vocabulario = [
        "python", "machine", "learning", "data", "science", "database", 
        "scalable", "distributed", "systems", "algorithm", "search", 
        "similarity", "jaccard", "minhash", "locality", "sensitive", "hashing"
    ]
    
    num_docs = 1000
    docs = {}
    random.seed(123)
    
    for i in range(num_docs):
        # Cria frases misturando palavras do vocabulário
        length = random.randint(10, 30)
        words = [random.choice(vocabulario) for _ in range(length)]
        docs[i] = " ".join(words)

    # Indexação
    num_hashes = 100
    bands = 20
    minhasher = MinHash(num_hashes=num_hashes)
    lsh = LSH(num_hashes=num_hashes, bands=bands)

    print(f"Indexando {num_docs} documentos...")
    doc_shingles = {}
    doc_signatures = {}
    
    start_time = time.time()
    for doc_id, text in docs.items():
        shingles = tokenize_and_shingle(text, k=2)
        doc_shingles[doc_id] = shingles
        sig = minhasher.compute_signature(shingles)
        doc_signatures[doc_id] = sig
        lsh.insert(doc_id, sig)
    index_time = time.time() - start_time
    print( levou = f"Tempo de indexação: {index_time:.4f}s")

    # Consulta e Validação de Recall
    queries = [random.choice(list(docs.keys())) for _ in range(50)]
    similarity_threshold = 0.3 # Limiar para considerarmos "similar"
    
    total_queries = len(queries)
    recall_sum = 0.0
    total_query_time = 0.0

    print("Executando consultas e medindo Recall e Latência...")
    for q_id in queries:
        q_sig = doc_signatures[q_id]
        q_shingles = doc_shingles[q_id]

        # 1. Busca Exata de Verdade (Ground Truth) para Jaccard >= threshold
        true_similar = set()
        for doc_id, shingles in doc_shingles.items():
            if doc_id == q_id:
                continue
            if jaccard_similarity(q_shingles, shingles) >= similarity_threshold:
                true_similar.add(doc_id)

        # 2. Busca via LSH + Filtragem por MinHash/Jaccard
        t0 = time.time()
        candidates = lsh.query(q_sig)
        
        # Refinamento de candidatos (calculando Jaccard real nos candidatos do LSH)
        lsh_results = set()
        for c_id in candidates:
            if c_id == q_id:
                continue
            if jaccard_similarity(q_shingles, doc_shingles[c_id]) >= similarity_threshold:
                lsh_results.add(c_id)
        t1 = time.time()
        
        total_query_time += (t1 - t0)

        # Cálculo do Recall para esta consulta
        if len(true_similar) > 0:
            found = len(true_similar.intersection(lsh_results))
            query_recall = found / len(true_similar)
            recall_sum += query_recall
        else:
            # Se não há verdadeiros similares, o recall é trivialmente 1.0 ou ignorado
            recall_sum += 1.0

    avg_recall = recall_sum / total_queries
    avg_query_time_ms = (total_query_time / total_queries) * 1000

    print(f"\n--- RESULTADOS DO EXPERIMENTO ---")
    print(f"Recall Médio: {avg_recall * 100:.2f}%")
    print(f"Tempo médio por consulta: {avg_query_time_ms:.4f} ms")

    # Asserções de Sucesso baseadas nos critérios da missão
    assert avg_recall >= 0.85, f"Falha no Recall: {avg_recall*100:.2f}% (Esperado >= 85%)"
    assert avg_query_time_ms < 50.0, f"Falha na Latência: {avg_query_time_ms:.2f}ms (Esperado < 50ms)"
    print("Sucesso! Todos os critérios da missão foram atingidos com folga.")

if __name__ == "__main__":
    run_experiment()