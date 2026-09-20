import numpy as np
from sklearn.metrics import f1_score

class ContextDataGenerator:
    """Gera dados sintéticos de contexto (embeddings) e rótulos de vazamento."""
    @staticmethod
    def generate(n_samples, seed=None, shift=0.0):
        if seed: np.random.seed(seed)
        # Classe 0: Contexto Seguro (centrado em 0)
        # Classe 1: Contexto com Vazamento (centrado em 2, com um 'shift' para testar generalização)
        X_safe = np.random.normal(0, 0.5, (n_samples // 2, 10))
        X_leak = np.random.normal(2 + shift, 0.5, (n_samples // 2, 10))
        
        X = np.vstack([X_safe, X_leak])
        y = np.hstack([np.zeros(n_samples // 2), np.ones(n_samples // 2)])
        
        # Shuffle
        indices = np.arange(n_samples)
        np.random.shuffle(indices)
        return X[indices], y[indices]

class LocalAgent:
    """Representa um agente em um pipeline distribuído."""
    def __init__(self, X, y):
        self.X = X
        self.y = y
        self.weights = np.zeros(10)
        self.bias = 0.0

    def train(self, global_weights, global_bias, lr=0.1, epochs=10):
        """Treino local usando SGD simples."""
        self.weights = global_weights.copy()
        self.bias = global_bias
        
        for _ in range(epochs):
            for i in range(len(self.X)):
                # Linear model: pred = dot(x, w) + b
                linear_model = np.dot(self.X[i], self.weights) + self.bias
                y_predicted = 1 / (1 + np.exp(-linear_model)) # Sigmoid
                
                # Gradient descent
                error = y_predicted - self.y[i]
                self.weights -= lr * error * self.X[i]
                self.bias -= lr * error
        
        return self.weights, self.bias

class FederatedServer:
    """Servidor central que agrega pesos e aplica Privacidade Diferencial."""
    def __init__(self, n_features):
        self.global_weights = np.zeros(n_features)
        self.global_bias = 0.0

    def aggregate(self, client_weights, client_biases, epsilon=None):
        """Agrega pesos (FedAvg) e aplica ruído DP se epsilon for fornecido."""
        avg_weights = np.mean(client_weights, axis=0)
        avg_bias = np.mean(client_biases)

        if epsilon is not None and epsilon > 0:
            # Simplificação pedagógica: O ruído é inversamente proporcional a epsilon.
            # Em DP real, o ruído depende da sensibilidade e do orçamento total.
            # Aqui, usamos sigma = 1/epsilon para demonstrar o impacto.
            sigma = 1.0 / epsilon
            noise_w = np.random.normal(0, sigma, size=avg_weights.shape)
            noise_b = np.random.normal(0, sigma)
            
            avg_weights += noise_w
            avg_bias += noise_b
            print(f"[Server] DP Aplicado: epsilon={epsilon:.2f}, sigma={sigma:.2f}")
        else:
            print("[Server] Sem DP aplicado (epsilon=inf)")

        self.global_weights = avg_weights
        self.global_bias = avg_bias

def run_experiment(epsilon_val):
    print(f"\n--- Iniciando Experimento: epsilon={epsilon_val} ---")
    
    # 1. Preparação de Dados
    # Agentes de Treino (Pipeline A, B, C)
    agents_data = []
    for i in range(3):
        X, y = ContextDataGenerator.generate(n_samples=100, seed=i)
        agents_data.append((X, y))
    
    # Agente de Teste (Pipeline D - Inédito/Held-out)
    # Note o 'shift=0.5' para simular uma distribuição de contexto levemente diferente
    X_test, y_test = ContextDataGenerator.generate(n_samples=100, seed=42, shift=0.5)

    server = FederatedServer(n_features=10)
    clients = [LocalAgent(X, y) for X, y in agents_data]

    # 2. Loop de Aprendizado Federado (Rounds)
    rounds = 5
    for r in range(rounds):
        client_weights = []
        client_biases = []
        
        for client in clients:
            w, b = client.train(server.global_weights, server.global_bias)
            client_weights.append(w)
            client_biases.append(b)
        
        server.aggregate(client_weights, client_biases, epsilon=epsilon_val)

    # 3. Avaliação no Agente Held-out
    final_w = server.global_weights
    final_b = server.global_bias
    
    # Predições
    logits = np.dot(X_test, final_w) + final_b
    predictions = (1 / (1 + np.exp(-logits)) > 0.5).astype(int)
    
    f1 = f1_score(y_test, predictions)
    print(f"Resultado Final -> F1 Score no Agente Inédito: {f1:.4f}")
    return f1

if __name__ == "__main__":
    # Caso 1: Sem Privacidade (Epsilon alto/infinito)
    f1_no_dp = run_experiment(epsilon_val=None)
    
    # Caso 2: Privacidade Alta (Epsilon baixo, muito ruído) - Desafio da Missão
    f1_high_dp = run_experiment(epsilon_val=0.4)
    
    # Caso 3: Privacidade Moderada
    f1_mod_dp = run_experiment(epsilon_val=2.0)

    print("\n" + "="*30)
    print("RESUMO DO EXPERIMENTO")
    print(f"F1 (Sem DP):      {f1_no_dp:.4f}")
    print(f"F1 (Epsilon 0.4): {f1_high_dp:.4f} (Alvo: > 0.85)")
    print(f"F1 (Epsilon 2.0): {f1_mod_dp:.4f}")
    print("="*30)
    
    # Verificação de sucesso para o ambiente de execução
    if f1_high_dp >= 0.85:
        print("SUCESSO: Critério de F1 atingido com DP restritivo.")
    else:
        print("AVISO: Critério de F1 não atingido com epsilon=0.4. O trade-off é real.")