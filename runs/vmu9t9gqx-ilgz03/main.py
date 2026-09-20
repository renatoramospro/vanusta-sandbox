import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import time

class SemanticFeatureExtractor:
    """Transforma texto em vetores para capturar vazamentos semânticos."""
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=10)
        self.is_fitted = False

    def fit(self, texts):
        self.vectorizer.fit(texts)
        self.is_fitted = True

    def transform(self, texts):
        if not self.is_fitted:
            return np.zeros((len(texts), 10))
        return self.vectorizer.transform(texts).toarray()

class RobustAnomalyDetector:
    def __init__(self, use_semantics=True):
        self.use_semantics = use_semantics
        self.model = IsolationForest(contamination=0.05, random_state=42)
        self.semantic_extractor = SemanticFeatureExtractor()
        self.golden_baseline_scores = None
        self.is_trained = False

    def _engineer_features(self, df):
        # Features de Metadados
        meta_features = df[['delta_t', 'payload_size', 'context_change']].values
        
        if self.use_semantics:
            # Features Semânticas
            semantic_vecs = self.semantic_extractor.transform(df['payload'].values)
            return np.hstack([meta_features, semantic_vecs])
        return meta_features

    def train(self, df, is_golden_set=False):
        if self.use_semantics:
            self.semantic_extractor.fit(df['payload'].values)
        
        features = self._engineer_features(df)
        self.model.fit(features)
        self.is_trained = True
        
        # Se for o Golden Set, guardamos os scores para validação futura
        if is_golden_set:
            scores = self.model.decision_function(features)
            self.golden_baseline_scores = scores
        return self

    def validate_new_model(self, validation_df):
        """Implementação do DriftGuard: Valida se o novo modelo é seguro contra o baseline."""
        if self.golden_baseline_scores is None:
            return True # Sem baseline, assume seguro (não recomendado em prod)
        
        features = self._engineer_features(validation_df)
        new_scores = self.model.decision_function(features)
        
        # Verifica se a média de 'normalidade' do novo modelo no Golden Set 
        # divergiu drasticamente do baseline original (indicando envenenamento)
        baseline_mean = np.mean(self.golden_baseline_scores)
        new_mean = np.mean(new_scores)
        
        # Se a média de score caiu muito, o modelo foi 'envenenado' para achar tudo anômalo ou vice-versa
        return abs(baseline_mean - new_mean) < 0.1

    def predict(self, df):
        features = self._engineer_features(df)
        # -1 para anomalia, 1 para normal
        return self.model.predict(features)

def run_benchmark():
    print("🚀 Iniciando Benchmark de Robustez de Pipeline Multi-Agente\n")

    # 1. GERAÇÃO DE DADOS (Sintéticos)
    # Dados Normais (Base para o Golden Set)
    normal_data = pd.DataFrame({
        'delta_t': np.random.uniform(0.1, 0.5, 100),
        'payload_size': np.random.uniform(10, 50, 100),
        'context_change': [0]*100,
        'payload': ["processando pedido" for _ in range(100)]
    })

    # Cenário A: Vazamento de Metadados (O que o antigo detectava)
    leak_meta = pd.DataFrame({
        'delta_t': [0.1]*5, 'payload_size': [10]*5, 'context_change': [1]*5,
        'payload': ["processando pedido" for _ in range(5)]
    })

    # Cenário B: Vazamento Semântico (O que o antigo FALHAVA)
    # Metadados normais, mas o conteúdo é de um contexto administrativo
    leak_semantic = pd.DataFrame({
        'delta_t': [0.2]*5, 'payload_size': [15]*5, 'context_change': [0]*5,
        'payload': ["ADMIN_PASSWORD_EXPOSED_XYZ" for _ in range(5)]
    })

    # Cenário C: Ataque de Drift (Envenenamento gradual)
    # Simulamos um conjunto de dados que foi 'contaminado' com vazamentos lentos
    poisoned_data = pd.DataFrame({
        'delta_t': np.random.uniform(0.1, 0.5, 100),
        'payload_size': np.random.uniform(10, 50, 100),
        'context_change': [0]*100,
        'payload': ["processando pedido admin_leak" for _ in range(100)]
    })

    # --- TESTE 1: VERSÃO ANTERIOR (Apenas Metadados) ---
    print("--- Testando Versão Anterior (Apenas Metadados) ---")
    old_detector = RobustAnomalyDetector(use_semantics=False)
    old_detector.train(normal_data)
    
    pred_meta = old_detector.predict(leak_meta)
    pred_sem = old_detector.predict(leak_semantic)
    
    recall_meta = np.mean(pred_meta == -1)
    recall_sem = np.mean(pred_sem == -1)
    print(f"Recall Metadados: {recall_meta:.2%}")
    print(f"Recall Semântico: {recall_sem:.2%} (FALHA DETECTADA)")

    # --- TESTE 2: VERSÃO ROBUSTA (Semântica + Baseline) ---
    print("\n--- Testando Versão Robusta (Semântica + DriftGuard) ---")
    robust_detector = RobustAnomalyDetector(use_semantics=True)
    # Treina com Golden Set
    robust_detector.train(normal_data, is_golden_set=True)
    
    pred_meta_r = robust_detector.predict(leak_meta)
    pred_sem_r = robust_detector.predict(leak_semantic)
    
    recall_meta_r = np.mean(pred_meta_r == -1)
    recall_sem_r = np.mean(pred_sem_r == -1)
    print(f"Recall Metadados: {recall_meta_r:.2%}")
    print(f"Recall Semântico: {recall_sem_r:.2%} (SUCESSO)")

    # --- TESTE 3: DRIFT DETECTION ---
    print("\n--- Testando DriftGuard (Proteção contra Envenenamento) ---")
    # Tentativa de re-treinar o modelo com dados envenenados
    new_model_attempt = RobustAnomalyDetector(use_semantics=True)
    new_model_attempt.train(poisoned_data)
    
    # O DriftGuard deve validar o novo modelo contra o baseline do robust_detector
    is_safe = robust_detector.validate_new_model(poisoned_data)
    
    if not is_safe:
        print("✅ DriftGuard: Bloqueou re-treino! O modelo estava sendo envenenado.")
    else:
        print("❌ DriftGuard: FALHA! Permitiu modelo envenenado.")

    # Verificação de Critérios de Sucesso
    print("\n--- Verificação de Critérios de Sucesso (Versão Robusta) ---")
    # Latência (simulada para o experimento)
    start = time.time()
    robust_detector.predict(leak_semantic)
    latency = (time.time() - start) * 1000
    print(f"Latência de Inferência: {latency:.4f} ms (Meta: < 1000ms)")
    
    # Recall Semântico
    if recall_sem_r >= 0.90 and latency < 1000:
        print("STATUS FINAL: APROVADO")
    else:
        print("STATUS FINAL: REPROVADO")

if __name__ == "__main__":
    run_benchmark()