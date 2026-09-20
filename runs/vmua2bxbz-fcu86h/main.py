import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, accuracy_score
from sklearn.dummy import DummyClassifier

def generate_vanusta_data(n_samples=1000, imbalance_ratio=0.1):
    """
    Gera dados sintéticos de churn para a Vanusta.
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
    
    # Aplicar desbalanceamento controlado
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
    df = generate_vanusta_data(n_samples=2000, imbalance_ratio=0.15)
    X = df.drop('churn', axis=1)
    y = df['churn']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print("=== EXPERIMENTO VANUSTA: DETECÇÃO DE CHURN ===")
    print(f"Amostras totais: {len(df)}")
    print(f"Distribuição de classes (Churn=1): {np.mean(y)*100:.1f}%")
    print("-" * 45)

    # 2. Contraexemplo: O erro da Acurácia (Modelo Dummy)
    # Este modelo sempre prevê a classe majoritária (0)
    dummy = DummyClassifier(strategy="most_frequent")
    dummy.fit(X_train, y_train)
    y_pred_dummy = dummy.predict(X_test)
    
    acc_dummy = accuracy_score(y_test, y_pred_dummy)
    f1_dummy = f1_score(y_test, y_pred_dummy)
    
    print(f"[CONTRAEXEMPLO] Modelo Dummy (Sempre 'Não Churn'):")
    print(f"  -> Acurácia: {acc_dummy:.4f} (Parece bom!)")
    print(f"  -> F1-Score: {f1_dummy:.4f} (É péssimo para o negócio!)")
    print("-" * 45)

    # 3. Implementação dos Modelos Reais
    results = []

    # Modelo A: Regressão Logística (Requer Escalonamento)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    lr = LogisticRegression(random_state=42)
    lr.fit(X_train_scaled, y_train)
    y_pred_lr = lr.predict(X_test_scaled)
    results.append({'modelo': 'Regressão Logística', 'f1': f1_score(y_test, y_pred_lr)})

    # Modelo B: Árvore de Decisão (Controle de Overfitting via max_depth)
    dt = DecisionTreeClassifier(max_depth=5, random_state=42)
    dt.fit(X_train, y_train)
    y_pred_dt = dt.predict(X_test)
    results.append({'modelo': 'Árvore de Decisão', 'f1': f1_score(y_test, y_pred_dt)})

    # Modelo C: Random Forest (Ensemble)
    rf = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    rf.fit(X_train, y_train)
    y_pred_rf = rf.predict(X_test)
    results.append({'modelo': 'Random Forest', 'f1': f1_score(y_test, y_pred_rf)})

    # 4. Exibição e Validação do Critério de Sucesso
    print("=== RESULTADOS DOS MODELOS ===")
    all_passed = True
    for res in results:
        status = "PASSOU" if res['f1'] >= 0.80 else "FALHOU"
        if res['f1'] < 0.80:
            all_passed = False
        print(f"{res['modelo']:20} | F1-Score: {res['f1']:.4f} | Status: {status}")
    
    print("-" * 45)
    if all_passed:
        print("VEREDITO: CRITÉRIO DE SUCESSO ATINGIDO (F1 >= 0.80)")
    else:
        print("VEREDITO: CRITÉRIO DE SUCESSO NÃO ATINGIDO")
        exit(1)

if __name__ == "__main__":
    run_experiment()