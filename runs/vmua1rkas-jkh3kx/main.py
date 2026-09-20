import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, f1_score

def generate_vanusta_data(n_samples=1000, churn_rate=0.15, random_state=42):
    """
    Gera dados sintéticos simulando clientes Vanusta.
    Features: tempo_contrato (meses), valor_mensal (R$), chamados_suporte (qtd).
    """
    np.random.seed(random_state)
    
    # Features base
    tempo_contrato = np.random.randint(1, 72, n_samples)
    valor_mensal = np.random.uniform(50, 500, n_samples)
    chamados_suporte = np.random.poisson(1, n_samples)
    
    # Criando uma relação lógica para o Churn (Target)
    # Churn aumenta se: contrato é curto, valor é alto e chamados são muitos
    logit = (
        -0.05 * tempo_contrato + 
        0.005 * valor_mensal + 
        0.8 * chamados_suporte - 
        3.0 # intercepto
    )
    prob = 1 / (1 + np.exp(-logit))
    
    # Ajustando para a taxa de churn desejada aproximadamente
    churn = (prob > np.percentile(prob, 100 * (1 - churn_rate))).astype(int)
    
    df = pd.DataFrame({
        'tempo_contrato': tempo_contrato,
        'valor_mensal': valor_mensal,
        'chamados_suporte': chamados_suporte,
        'churn': churn
    })
    return df

def run_experiment():
    print("--- INICIANDO EXPERIMENTO VANUSTA: DETECÇÃO DE CHURN ---")
    
    # 1. Preparação de Dados
    df = generate_vanusta_data(n_samples=2000, churn_rate=0.20)
    X = df.drop('churn', axis=1)
    y = df['churn']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
    
    # Escalonamento (Crucial para Regressão Logística)
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
    
    print(f"Dataset: {len(df)} amostras | Taxa de Churn: {df['churn'].mean():.2%}")
    print("-" * 50)

    # 3. Treinamento e Avaliação
    for name, model in models.items():
        # Usamos os dados escalonados para todos para manter consistência no experimento
        model.fit(X_train_scaled, y_train)
        y_pred = model.predict(X_test_scaled)
        
        f1 = f1_score(y_test, y_pred)
        results[name] = f1
        
        print(f"\n[MODELO: {name}]")
        print(f"F1-Score: {f1:.4f}")
        print("Relatório de Classificação:")
        print(classification_report(y_test, y_pred, zero_division=0))

    # 4. Validação do Critério de Sucesso
    avg_f1 = np.mean(list(results.values()))
    print("-" * 50)
    print(f"F1-Score Médio dos Modelos: {avg_f1:.4f}")
    
    # Ataque ao equívoco: Demonstrando a falha da Acurácia
    # Criando um modelo "burro" que sempre prevê 0 (não churn)
    y_dumb_pred = np.zeros_like(y_test)
    dumb_accuracy = (y_dumb_pred == y_test).mean()
    dumb_f1 = f1_score(y_test, y_dumb_pred, zero_division=0)
    
    print(f"\n[CONTRAEXEMPLO: Modelo 'Burro' (Sempre prevê 0)]")
    print(f"Acurácia do Modelo Burro: {dumb_accuracy:.4f} (Parece bom!)")
    print(f"F1-Score do Modelo Burro: {dumb_f1:.4f} (É péssimo!)")
    print("Conclusão: A acurácia engana em dados desbalanceados.")
    print("-" * 50)

    if avg_f1 >= 0.80:
        print("STATUS: CRITÉRIO DE SUCESSO ATINGIDO (F1-Score Médio >= 0.80)")
    else:
        print("STATUS: CRITÉRIO DE SUCESSO NÃO ATINGIDO")

if __name__ == "__main__":
    run_experiment()