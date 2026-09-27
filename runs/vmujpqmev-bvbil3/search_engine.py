import math
import re
from collections import defaultdict, Counter

class SearchEngine:
    STOP_WORDS = {"de", "a", "o", "que", "e", "do", "da", "em", "um", "para", "é", "com", "não", "uma", "os", "no", "se", "na", "por", "mais", "as", "dos", "como", "mas", "foi", "ao", "ele", "das", "seu", "sua", "ou", "quando", "muito", "nos", "já", "está", "eu", "também", "só", "pelo", "pela", "até", "is", "the", "and", "to", "of", "in", "for", "on", "with"}

    def __init__(self):
        self.documents = {}  # doc_id -> texto original
        self.doc_lengths = {} # doc_id -> total de termos tokenizados
        self.inverted_index = defaultdict(set) # termo -> conjunto de doc_ids
        self.term_freqs = defaultdict(Counter) # doc_id -> Counter(termo)
        self.idf_cache = {}
        self.N = 0

    def tokenize(self, text: str) -> list:
        # Equívoco comum evitado: tokenizar apenas por espaço mantém pontuação colada.
        # Usamos regex para extrair apenas palavras alfanuméricas e converter para minúsculas.
        tokens = re.findall(r'\b\w+\b', text.lower())
        return [t for t in tokens if t not in self.STOP_WORDS and len(t) > 1]

    def add_document(self, doc_id: int, text: str):
        self.documents[doc_id] = text
        tokens = self.tokenize(text)
        self.doc_lengths[doc_id] = len(tokens)
        
        tf = Counter(tokens)
        self.term_freqs[doc_id] = tf
        
        for term in tf.keys():
            self.inverted_index[term].add(doc_id)
            
        self.N = len(self.documents)
        self.idf_cache.clear() # Invalida cache de IDF

    def _get_idf(self, term: str) -> float:
        if term in self.idf_cache:
            return self.idf_cache[term]
        
        # IDF com suavização padrão (Smooth IDF)
        df = len(self.inverted_index[term])
        idf = math.log(1.0 + (self.N - df + 0.5) / (df + 0.5))
        self.idf_cache[term] = idf
        return idf

    def search_tfidf(self, query: str, top_k: int = 5):
        query_tokens = self.tokenize(query)
        if not query_tokens:
            return []

        scores = defaultdict(float)
        query_tf = Counter(query_tokens)

        for term in query_tf:
            if term not in self.inverted_index:
                continue
            idf = self._get_idf(term)
            for doc_id in self.inverted_index[term]:
                # TF bruto normalizado pelo comprimento do documento
                tf = self.term_freqs[doc_id][term] / self.doc_lengths[doc_id]
                scores[doc_id] += tf * idf

        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [(doc_id, score) for doc_id, score in sorted_docs[:top_k]]

    def search_boolean(self, term1: str, op: str, term2: str) -> set:
        t1 = term1.lower()
        t2 = term2.lower()
        
        set1 = self.inverted_index.get(t1, set())
        set2 = self.inverted_index.get(t2, set())

        if op == "AND":
            return set1.intersection(set2)
        elif op == "OR":
            return set1.union(set2)
        elif op == "NOT":
            return set1.difference(set2)
        else:
            raise ValueError(f"Operador desconhecido: {op}")

if __name__ == "__main__":
    engine = SearchEngine()

    # Indexando documentos de teste
    docs = {
        1: "O rato roeu a roupa do rei de Roma. Rato veloz.",
        2: "A programação de computadores exige lógica e estruturas de dados eficientes.",
        3: "O motor de busca utiliza índice invertido para pesquisa textual rápida.",
        4: "Computadores modernos processam dados estruturados e texto com alta performance."
    }

    for doc_id, text in docs.items():
        engine.add_document(doc_id, text)

    print(f"Total de documentos indexados: {engine.N}")

    # Teste 1: Busca TF-IDF
    query = "busca textual índice"
    results = engine.search_tfidf(query)
    print(f"\nResultados TF-IDF para '{query}':")
    for doc_id, score in results:
        print(f" - Doc {doc_id} (Score: {score:.4f}): {docs[doc_id]}")
    
    assert results[0][0] == 3, "O documento 3 deveria ser o mais relevante para a consulta de busca textual!"

    # Teste 2: Busca Booleana (AND)
    bool_res = engine.search_boolean("computadores", "AND", "dados")
    print(f"\nBusca Booleana ('computadores' AND 'dados'): Docs {bool_res}")
    assert bool_res == {2, 4}, "Apenas documentos 2 e 4 contêm ambos os termos."

    # Teste 3: Contraexemplo do equívoco comum (Tokenização ingênua vs Regex)
    # Tokenização por espaço falharia com pontuação grudada (ex: "Roma.")
    tokens_com_pontuacao = engine.tokenize("Roma. Rato, veloz!")
    print(f"\nTokens limpos com regex (evitando pontuação colada): {tokens_com_pontuacao}")
    assert "roma" in tokens_com_pontuacao and "ponto" not in "".join(tokens_com_pontuacao)

    print("\n[SUCESSO] Todos os testes executados com código 0 e assertivas validadas!")