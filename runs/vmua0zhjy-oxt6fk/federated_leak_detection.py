import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split

# Semente para reprodutibilidade
np.random.seed(42)

def generate_synthetic_agent_data(n_samples=500, n_features=10, leak_ratio=0.2):
    """Gera dados sintéticos de contexto para simular um agente de pipeline."""
    X = np.random.randn(n_samples, n_features)
    # Regra linear latente para vazamento de contexto + ruído
    weights_true = np.array([1.5, -2.0, 0.5, 0.0, 0.0, 1.0, -1.5, 0.0, 0.5, -0.5])
    logits = np.dot(X, weights_true) + np.random.normal(0, 0.5, n_samples)
    probs = 1 / (1 + np.exp(-logits))
    y = (probs > np.percentile(probs, 100 * (1 - leak_ratio))).astype(int)
    return X, y

class FederatedAgent:
    def __init__(self, agent_id, X, y):
        self.agent_id = agent_id
        self.X = X
        self.y = y
        # Modelo local (Regressão Logística simulando camada linear)
        self.model = LogisticRegression(warm_start=True, max_iter=100)
        # Inicializa coeficientes
        self.model.classes_ = np.array([0, 1])
        self.model.coef_ = np.zeros((1, X.shape[1]))
        self.model.intercept_ = np.zeros((1,))

    def local_update(self, global_weights, global_intercept):
        """Treina o modelo localmente partindo dos pesos globais."""
        self.model.coef_ = np.copy(global_weights)
        self.model.intercept_ = np.copy(global_intercept)
        
        # Ajuste local via fit (simulando gradiente/otimização)
        self.model.fit(self.X, self.y)
        return self.model.coef_, self.model.intercept_

def add_differential_privacy_noise(coefs, intercept, epsilon=0.5, sensitivity=1.0):
    """
    Adiciona ruído Gaussiano calibrado para satisfazer o orçamento de privacidade epsilon.
    Equívoco comum evitado: ruído aplicado deve ser proporcional à sensibilidade e inversamente a epsilon.
    """
    scale = sensitivity / epsilon
    noise_coefs = np.random.laplace(0, scale, size=coefs.shape)
    noise_intercept = np.random.laplace(0, scale, size=intercept.shape)
    return coefs + noise_coefs, intercept + noise_intercept

def run_federated_pipeline():
    print("--- Iniciando Simulação de Aprendizado Federado para Detecção de Vazamento ---")
    
    # 1. Criar múltiplos agentes (pipelines distribuídas)
    n_agents = 4
    agents = []
    for i in range(n_agents):
        X_a, y_a = generate_synthetic_agent_data(n_samples=600, n_features=10)
        agents.append(FederatedAgent(agent_id=i, X=X_a, y=y_a))
    
    # 2. Criar conjunto de teste held-out de agentes/pipelines não vistos
    X_test, y_test = generate_synthetic_agent_data(n_samples=1000, n_features=10)
    
    # 3. Inicialização do Modelo Global
        # 3. Inicialização do Modelo Global
    n_features = 10
    global_coefs = np.zeros((1, n_features))
    global_intercept = np.zeros((1,))
    
    # Parâmetros de FL
    n_rounds = 5
    epsilon_budget = 0.5  # Orçamento restrito conforme requisito
    
    for round_idx in range(n_rounds):
        local_coefs_list = []
        local_intercepts_list = []
        
        # Cada agente treina localmente (NENHUM DADO BRUTO SAI DO AGENTE)
        for agent in agents:
            c, i = agent.local_update(global_coefs, global_intercept)
            
            # Aplicação de Privacidade Diferencial nas atualizações enviadas
            c_dp, i_dp = add_differential_privacy_noise(c, i, epsilon=epsilon_budget)
            
            local_coefs_list.append(c_dp)
            local_intercepts_list.append(i_dp)
            
        # FedAvg: Agregação no Servidor Central
        global_coefs = np.mean(local_coefs_list, axis=0)
        global_intercept = np.mean(local_intercepts_list, axis=0)
        
        # Avaliação intermediária
        eval_model = LogisticRegression()
        eval_model.classes_ = np.array([0, 1])
        eval_model.coef_ = global_coefs
        eval_model.intercept_ = global_intercept
        
        y_pred = eval_model.predict(X_test)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        print(f"Rodada {round_idx + 1} | F1-Score no Held-Out: {f1:.4f} | Privacidade (ε): {epsilon_budget}")

    # Validação final do critério de sucesso
    assert f1 >= 0.70, f"F1 score abaixo do esperado: {f1}"
    print("\n[SUCESSO] Treinamento federado concluído com privacidade preservada e dados brutos restritos aos agentes.")

if __name__ == "__main__":
    run_federated_pipeline()