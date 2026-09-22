import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, recall_score

# Carregar dados históricos
df = pd.read_csv('dados_historicos.csv')

# Dividir dados em treino e teste
X_train, X_test, y_train, y_test = train_test_split(df.drop('falha', axis=1), df['falha'], test_size=0.2, random_state=42)

# Treinar modelo de probabilidade de falha
modelo_probabilidade = RandomForestClassifier(n_estimators=100, random_state=42)
modelo_probabilidade.fit(X_train, y_train)

# Prever probabilidade de falha em dados de teste
y_pred_probabilidade = modelo_probabilidade.predict_proba(X_test)[:, 1]

# Avaliar modelo de probabilidade de falha
f1_score_probabilidade = f1_score(y_test, (y_pred_probabilidade > 0.5).astype(int), average='binary')
recall_score_probabilidade = recall_score(y_test, (y_pred_probabilidade > 0.5).astype(int), average='binary')

# Treinar modelo de impacto
modelo_impacto = RandomForestRegressor(n_estimators=100, random_state=42)
modelo_impacto.fit(X_train, df['impacto'])

# Prever impacto em dados de teste
y_pred_impacto = modelo_impacto.predict(X_test)

# Avaliar modelo de impacto
f1_score_impacto = f1_score(y_test, (y_pred_impacto > 0.5).astype(int), average='binary')
recall_score_impacto = recall_score(y_test, (y_pred_impacto > 0.5).astype(int), average='binary')

# Gerar plano de mitigação
plano_mitigacao = {
    'circuit_breakers': ['circuit_breaker_1', 'circuit_breaker_2'],
    'fallbacks': ['fallback_1', 'fallback_2'],
    'alertas': ['alerta_1', 'alerta_2'],
    'politicas_retransmissao': ['politica_1', 'politica_2']
}

# Imprimir resultados
print('F1-Score Probabilidade de Falha:', f1_score_probabilidade)
print('Recall Probabilidade de Falha:', recall_score_probabilidade)
print('F1-Score Impacto:', f1_score_impacto)
print('Recall Impacto:', recall_score_impacto)
print('Plano de Mitigação:', plano_mitigacao)