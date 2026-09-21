import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

def simular_dados_projetos(n_amostras=1000, seed=42):
    np.random.seed(seed)
    
    # Features:
    # 1. Complexidade Ciclomática Média (1 a 15)
    complexidade = np.random.uniform(1.0, 15.0, n_amostras)
    
    # 2. MTTR (Mean Time to Resolution de bugs em dias) (1 a 30)
    mttr = np.random.exponential(scale=5.0, size=n_amostras) + 1.0
    
    # 3. Taxa de Churn de Commits (linhas modificadas por commit) (10 a 500)
    churn = np.random.gamma(shape=2.0, scale=50.0, size=n_amostras) + 10.0
    
    # Regra lógica para definir o risco real de atraso (Atrasado = 1, No Prazo = 0)
    # Projetos com alta complexidade, alto MTTR e alto churn têm maior probabilidade de atrasar.
    score_risco = (
        0.3 * (complexidade / 15.0) + 
        0.4 * (mttr / 30.0) + 
        0.3 * (churn / 500.0) +
        np.random.normal(0, 0.05, n_amostras) # Ruído
    )
    
    # Definimos limiar para que a classe de atrasos seja minoritária (ex: ~20% dos projetos atrasam)
    atrasado = (score_risco > 0.48).astype(int)
    
    X = np.column_stack((complexidade, mttr, churn))
    return X, atrasado

def executar_experimento():
    print("--- INICIANDO SIMULAÇÃO DO MODELO PREDITIVO DE RISCO ---")
    X, y = simular_dados_projetos(n_amostras=2000)
    
    print(f"Total de projetos simulados: {len(y)}")
    print(f"Projetos com atraso real (Classe 1): {np.sum(y)} ({np.mean(y)*100:.1f}%)")
    print(f"Projetos no prazo (Classe 0): {len(y) - np.sum(y)} ({(1 - np.mean(y))*100:.1f}%)\n")
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
    
    modelo = RandomForestClassifier(n_estimators=100, random_state=42)
    modelo.fit(X_train, y_train)
    
    y_pred = modelo.predict(X_test)
    
    acuracia = accuracy_score(y_test, y_pred)
    precisao = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    
    print("--- RESULTADOS DA AVALIAÇÃO DO MODELO ---")
    print(f"Acurácia : {acuracia:.4f} (Cuidado: pode ser enganosa se desbalanceada)")
    print(f"Precisão : {precisao:.4f} (Proporção de alertas de atraso que foram corretos)")
    print(f"Recall   : {recall:.4f}   (Capacidade de capturar os projetos que realmente atrasaram)")
    print(f"F1-Score : {f1:.4f}   (Média harmônica entre Precisão e Recall)")
    
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
    print("\n--- MATRIZ DE CONFUSÃO ---")
    print(f"Verdadeiros Negativos (Seguros corretos): {tn}")
    print(f"Falsos Positivos     (Alarmes falsos)    : {fp}")
    print(f"Falsos Negativos     (Surpresas de atraso): {fn} <-- PERIGO CRÍTICO PARA O NEGÓCIO")
    print(f"Verdadeiros Positivos(Atrasos prevenidos): {tp}")
    
    # Validação rigorosa contra o critério aprimorado
    assert recall >= 0.80, f"Falha no Recall: {recall:.2f} está abaixo do limite de 0.80"
    assert f1 >= 0.75, f"Falha no F1-Score: {f1:.2f} está abaixo do esperado"
    print("\n[SUCESSO] O experimento validou com sucesso as métricas críticas de risco!")

if __name__ == "__main__":
    executar_experimento()