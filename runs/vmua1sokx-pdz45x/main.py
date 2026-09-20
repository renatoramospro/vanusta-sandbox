import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, f1_score, accuracy_score

def generate_vanusta_data(n_samples=1000, churn_rate=0.15, random_state=42):
    """Gera dados sintéticos simulando churn de clientes Vanusta."""
    np.random.seed(random_state)
    
    # Features
    tenure = np.random.randint(1, 72, n_samples)
    monthly_charges = np.random.uniform(20, 120, n_samples)
    support_calls = np.random.poisson(1, n_samples)
    
    # Criar uma relação lógica para o churn (mais chamados + menos tenure = mais churn)
    # Logit score: base + coef_tenure*tenure + coef_calls*calls + noise
    logit = -2 + (0.02 * tenure) - (0.8 * support_calls) + (0.01 * monthly_charges)
    prob = 1 / (1 + np.exp(-logit))
    
    # Ajustar para a taxa de churn desejada (aproximadamente)
    churn = (prob > np.percentile(prob, 100 * (1 - churn_rate))).astype(int)
    
    df = pd.DataFrame({
        'tenure': tenure,
        'monthly_charges': monthly_charges,
        'support_calls': support_calls,
        'churn': churn
    })
    return df

def run_experiment():
    print("=== INICIANDO EXPERIMENTO VANUSTA: DETECÇÃO DE CHURN ===\n")
    
    # 1. Preparação
    df = generate_vanusta_data(n_samples=1500, churn_rate=0.15)
    X = df.drop('churn', axis=1)
    y = df['churn']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Escalonamento (Essencial para Regressão Logística)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 2. Definição dos Modelos
    models = {
        "Regressão Logística": LogisticRegression(random_state=42),
        "Árvore de Decisão": DecisionTreeClassifier(max_depth=5, random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    }

    results = {}

    # 3. Treinamento e Avaliação
    print("--- Avaliação dos Modelos ---")
    for name, model in models.items():
        # Usar dados escalonados para todos para simplificar o experimento, 
        # embora árvores não precisem tecnicamente de escala.
        model.fit(X_train_scaled, y_train)
        y_pred = model.predict(X_test_scaled)
        
        f1 = f1_score(y_test, y_pred)
        acc = accuracy_score(y_test, y_pred)
        results[name] = f1
        
        print(f"\n[{name}]")
        print(f"Acurácia: {acc:.4f}")
        print(f"F1-Score: {f1:.4f}")
        print("Relatório de Classificação:")
        print(classification_report(y_test, y_pred, zero_division=0))

    # 4. Validação do Critério de Sucesso
    avg_f1 = np.mean(list(results.values()))
    print(f"\n>>> F1-Score Médio: {avg_f1:.4f}")
    if avg_f1 >= 0.80:
        print("STATUS: CRITÉRIO DE SUCESSO ATINGIDO (F1-Score >= 0.80)")
    else:
        print("STATUS: CRITÉRIO DE SUCESSO NÃO ATINGIDO")

    # 5. Ataque ao Equívoco: O perigo da Acurácia
    print("\n--- ATAQUE AO EQUÍVOCO: Por que Acurácia é enganosa? ---")
    # Modelo "Burro": Sempre prevê que NINGUÉM vai dar churn (classe majoritária)
    y_pred_dumb = np.zeros_like(y_test)
    dumb_acc = accuracy_score(y_test, y_pred_dumb)
    dumb_f1 = f1_score(y_test, y_pred_dumb)
    
    print(f"Modelo 'Sempre Não-Churn' -> Acurácia: {dumb_acc:.4f} | F1-Score: {dumb_f1:.4f}")
    print(f"Nota: O modelo tem alta acurácia, mas F1 de 0.0, sendo inútil para detectar churn.")

if __name__ == "__main__":
    run_experiment()