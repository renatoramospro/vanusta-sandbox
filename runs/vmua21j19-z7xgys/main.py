import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, accuracy_score
from sklearn.pipeline import Pipeline

def generate_vanusta_data(n_samples=1000, random_state=42):
    """Gera dados sintéticos de churn com correlações lógicas."""
    np.random.seed(random_state)
    
    tenure = np.random.randint(1, 72, n_samples)
    support_calls = np.random.poisson(1.5, n_samples)
    monthly_charges = np.random.uniform(20, 120, n_samples)
    
    # Lógica de Churn: Mais chamados e menos tenure aumentam o risco
    # Logit: intercept - (coef_tenure * tenure) + (coef_calls * calls)
    logit = -1.0 - (0.08 * tenure) + (1.5 * support_calls)
    prob = 1 / (1 + np.exp(-logit))
    
    # Gerar target baseado na probabilidade
    y = (np.random.rand(n_samples) < prob).astype(int)
    
    df = pd.DataFrame({
        'tenure': tenure,
        'support_calls': support_calls,
        'monthly_charges': monthly_charges,
        'churn': y
    })
    return df

def run_experiment():
    # 1. Preparação
    df = generate_vanusta_data()
    X = df.drop('churn', axis=1)
    y = df['churn']
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"--- Configuração do Experimento ---")
    print(f"Amostras totais: {len(df)}")
    print(f"Taxa de Churn no dataset: {df['churn'].mean():.2%}\n")

    # 2. Definição dos Modelos
    models = {
        "Regressão Logística (Linear)": Pipeline([
            ('scaler', StandardScaler()),
            ('clf', LogisticRegression())
        ]),
        "Árvore de Decisão (Non-Linear)": DecisionTreeClassifier(max_depth=5, random_state=42),
        "Random Forest (Ensemble)": RandomForestClassifier(n_estimators=100, random_state=42)
    }

    # 3. Treinamento e Avaliação
    results = []
    print(f"--- Resultados dos Modelos ---")
    
    for name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        
        results.append({"modelo": name, "f1": f1, "acc": acc})
        print(f"{name:30} | Acc: {acc:.4f} | F1: {f1:.4f}")

    # 4. Ataque ao Equívoco (Modelo Dummy/Burro)
    # Um modelo que sempre prevê 0 (não churn)
    y_pred_dumb = np.zeros_like(y_test)
    dumb_acc = accuracy_score(y_test, y_pred_dumb)
    dumb_f1 = f1_score(y_test, y_pred_dumb)
    
    print(f"\n--- Contraexemplo: Modelo 'Sempre Não-Churn' ---")
    print(f"Modelo Dummy           | Acc: {dumb_acc:.4f} | F1: {dumb_f1:.4f}")
    print("Nota: A alta acurácia do modelo dummy esconde sua incapacidade de detectar churn.")

    # 5. Validação do Critério de Sucesso
    print(f"\n--- Validação do Critério de Sucesso (F1 >= 0.80) ---")
    all_passed = True
    for res in results:
        status = "PASSOU" if res['f1'] >= 0.80 else "FALHOU"
        if res['f1'] < 0.80: all_passed = False
        print(f"{res['modelo']:30} -> F1: {res['f1']:.4f} [{status}]")
    
    if all_passed:
        print("\nRESULTADO FINAL: MISSÃO CUMPRIDA (Média de F1 >= 0.80)")
    else:
        print("\nRESULTADO FINAL: MISSÃO FALHOU (Algum modelo abaixo de 0.80)")
        exit(1)

if __name__ == "__main__":
    run_experiment()