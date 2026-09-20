import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, accuracy_score

def generate_vanusta_data(n_samples=1200, churn_rate=0.15, random_state=42):
    """Gera dados sintéticos simulando churn de clientes Vanusta."""
    np.random.seed(random_state)
    
    # Features
    tenure = np.random.randint(1, 72, n_samples)
    monthly_charges = np.random.uniform(20, 120, n_samples)
    support_calls = np.random.poisson(1.5, n_samples)
    
    # Criar uma relação lógica para o churn:
    # Mais chamados de suporte (+) e menos tempo de casa (-) aumentam o churn.
    # Logit = intercept + c1*tenure + c2*calls + c3*charges
    logit = -2.5 - (0.05 * tenure) + (0.8 * support_calls) + (0.01 * monthly_charges)
    prob = 1 / (1 + np.exp(-logit))
    
    # Gerar target baseado na probabilidade
    y = (np.random.rand(n_samples) < prob).astype(int)
    
    # Ajustar para garantir que a taxa de churn seja próxima ao desejado
    # (Em dados reais, o desbalanceamento é uma característica, não um ajuste)
    
    df = pd.DataFrame({
        'tenure': tenure,
        'monthly_charges': monthly_charges,
        'support_calls': support_calls,
        'churn': y
    })
    return df

def run_experiment():
    print("--- Iniciando Experimento Vanusta: Detecção de Churn ---")
    
    # 1. Preparação de Dados
    df = generate_vanusta_data()
    X = df.drop('churn', axis=1)
    y = df['churn']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # 2. Pré-processamento (Escalonamento para modelos lineares)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # 3. Treinamento de Modelos
    models = {
        "Regressão Logística": LogisticRegression(random_state=42),
        "Árvore de Decisão": DecisionTreeClassifier(max_depth=5, random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    }
    
    results = {}
    
    print(f"Dados: {len(df)} amostras | Taxa de Churn Real: {df['churn'].mean():.2%}")
    print("-" * 50)

    for name, model in models.items():
        # Usar dados escalonados para Logística, dados originais para Árvores (invariantes à escala)
        if name == "Regressão Logística":
            model.fit(X_train_scaled, y_train)
            preds = model.predict(X_test_scaled)
        else:
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            
        f1 = f1_score(y_test, preds)
        acc = accuracy_score(y_test, preds)
        results[name] = f1
        print(f"[{name}] -> F1-Score: {f1:.4f} | Acurácia: {acc:.4f}")

    # 4. Ataque ao Equívoco: O Modelo "Burro" (Sempre prevê Não-Churn)
    y_pred_dumb = np.zeros_like(y_test)
    dumb_f1 = f1_score(y_test, y_pred_dumb)
    dumb_acc = accuracy_score(y_test, y_pred_dumb)
    
    print("-" * 50)
    print(f"Modelo 'Sempre Não-Churn' -> Acurácia: {dumb_acc:.4f} | F1-Score: {dumb_f1:.4f}")
    print("Nota: O modelo tem alta acurácia, mas F1 de 0.0, sendo inútil para o negócio.")
    print("-" * 50)

    # 5. Validação do Critério de Sucesso
    min_f1_threshold = 0.80
    success = all(score >= min_f1_threshold for score in results.values())
    
    if success:
        print("RESULTADO: CRITÉRIO DE SUCESSO ATINGIDO (Média F1 >= 80%)")
    else:
        print(f"RESULTADO: CRITÉRIO NÃO ATINGIDO (Mínimo F1 esperado: {min_f1_threshold})")
        print(f"Melhor F1 obtido: {max(results.values()):.4f}")

if __name__ == "__main__":
    run_experiment()