import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, accuracy_score

def generate_vanusta_data(n_samples=1000, imbalance_ratio=0.1):
    """
    Gera dados sintéticos de churn para o domínio Vanusta.
    Features: tenure (meses), monthly_charges (valor), support_calls (chamados).
    """
    np.random.seed(42)
    
    tenure = np.random.randint(1, 72, n_samples)
    monthly_charges = np.random.uniform(20, 120, n_samples)
    support_calls = np.random.poisson(1, n_samples)
    
    # Lógica de churn: mais chamados e menos tempo de contrato aumentam o risco
    # Logit: -2 + 0.02*tenure - 0.8*calls + 0.01*charges
    logit = -2 + (0.02 * tenure) - (0.8 * support_calls) + (0.01 * monthly_charges)
    prob = 1 / (1 + np.exp(-logit))
    
    # Aplicar o desbalanceamento solicitado
    y = (prob > np.percentile(prob, 100 * (1 - imbalance_ratio))).astype(int)
    
    df = pd.DataFrame({
        'tenure': tenure,
        'monthly_charges': monthly_charges,
        'support_calls': support_calls,
        'churn': y
    })
    return df

def run_experiment():
    # 1. Preparação dos Dados
    df = generate_vanusta_data(n_samples=1500, imbalance_ratio=0.15)
    X = df.drop('churn', axis=1)
    y = df['churn']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # 2. Baseline: Modelo "Dummy" (Sempre prevê não-churn)
    # Demonstra o erro de usar Acurácia em dados desbalanceados
    y_dummy = np.zeros_like(y_test)
    acc_dummy = accuracy_score(y_test, y_dummy)
    f1_dummy = f1_score(y_test, y_dummy, zero_division=0)
    
    print(f"--- [BASELINE] Modelo Dummy (Sempre 'Não-Churn') ---")
    print(f"Acurácia: {acc_dummy:.4f}")
    print(f"F1-Score: {f1_dummy:.4f} (O modelo falha totalmente em detectar churn)\n")

    # 3. Implementação dos 3 Algoritmos Reais
    results = []

    # Modelo A: Regressão Logística (Requer Escalonamento)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    lr = LogisticRegression(random_state=42)
    lr.fit(X_train_scaled, y_train)
    y_pred_lr = lr.predict(X_test_scaled)
    results.append({
        'modelo': 'Regressão Logística',
        'f1': f1_score(y_test, y_pred_lr),
        'acc': accuracy_score(y_test, y_pred_lr)
    })

    # Modelo B: Árvore de Decisão (Controle de Overfitting via max_depth)
    dt = DecisionTreeClassifier(max_depth=5, random_state=42)
    dt.fit(X_train, y_train)
    y_pred_dt = dt.predict(X_test)
    results.append({
        'modelo': 'Árvore de Decisão',
        'f1': f1_score(y_test, y_pred_dt),
        'acc': accuracy_score(y_test, y_pred_dt)
    })

    # Modelo C: Random Forest (Ensemble)
    rf = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    rf.fit(X_train, y_train)
    y_pred_rf = rf.predict(X_test)
    results.append({
        'modelo': 'Random Forest',
        'f1': f1_score(y_test, y_pred_rf),
        'acc': accuracy_score(y_test, y_pred_rf)
    })

    # 4. Exibição e Validação do Critério de Sucesso
    print(f"--- [RESULTADOS] Modelos de ML ---")
    print(f"{'Modelo':<20} | {'Acurácia':<10} | {'F1-Score':<10}")
    print("-" * 45)
    
    all_passed = True
    for res in results:
        status = "PASSOU" if res['f1'] >= 0.80 else "FALHOU"
        if res['f1'] < 0.80:
            all_passed = False
        print(f"{res['modelo']:<20} | {res['acc']:<10.4f} | {res['f1']:<10.4f} [{status}]")

    print("\n--- [VERIFICAÇÃO FINAL] ---")
    if all_passed:
        print("CRITÉRIO DE SUCESSO ATINGIDO: Média de F1-Score >= 0.80")
    else:
        print("CRITÉRIO DE SUCESSO NÃO ATINGIDO.")
        exit(1)

if __name__ == "__main__":
    run_experiment()