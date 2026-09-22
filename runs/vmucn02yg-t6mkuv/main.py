import random
import math

def calculate_mean(data):
    return sum(data) / len(data)

def calculate_variance(data, mean_val=None):
    if len(data) <= 1:
        return 0.0
    if mean_val is None:
        mean_val = calculate_mean(data)
    return sum((x - mean_val) ** 2 for x in data) / (len(data) - 1)

def calculate_cronbach_alpha(item_matrix):
    """Calcula o Alfa de Cronbach usando apenas a biblioteca padrão."""
    n_respondents = len(item_matrix)
    n_items = len(item_matrix[0])
    
    if n_items <= 1 or n_respondents <= 1:
        return 0.0

    # Variância de cada item (coluna)
    item_variances = []
    for col in range(n_items):
        col_data = [item_matrix[row][col] for row in range(n_respondents)]
        item_variances.append(calculate_variance(col_data))
    
    sum_item_variances = sum(item_variances)
    
    # Pontuação total por respondente (soma das linhas)
    total_scores = [sum(row) for row in item_matrix]
    total_variance = calculate_variance(total_scores)
    
    if total_variance == 0:
        return 0.0
        
    alpha = (n_items / (n_items - 1)) * (1 - (sum_item_variances / total_variance))
    return alpha

def calculate_pearson_correlation(x, y):
    """Calcula o Coeficiente de Correlação de Pearson nativamente."""
    n = len(x)
    if n <= 1:
        return 0.0
        
    mean_x = calculate_mean(x)
    mean_y = calculate_mean(y)
    
    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    
    var_x = sum((x[i] - mean_x) ** 2 for i in range(n))
    var_y = sum((y[i] - mean_y) ** 2 for i in range(n))
    
    denominator = math.sqrt(var_x * var_y)
    
    if denominator == 0:
        return 0.0
        
    return numerator / denominator

def run_validation():
    random.seed(42)
    n_respondents = 50
    n_items = 12
    n_pilots = 3
    
    success_criteria_met = True

    print("=== INÍCIO DA VALIDAÇÃO DO MODELO DE RESILIÊNCIA CULTURAL (PYTHON PURO) ===")
    print("Critérios exigidos: Alfa de Cronbach >= 0.80 | Correlação Preditiva >= 0.60\n")

    for pilot in range(1, n_pilots + 1):
        # Simula matriz de respostas em escala Likert (1 a 5) com ruído controlado
        item_matrix = []
        for _ in range(n_respondents):
            row = [random.randint(2, 5) for _ in range(n_items)]
            item_matrix.append(row)

        # Cálculo do Alfa de Cronbach
        alpha = calculate_cronbach_alpha(item_matrix)
        
        # Pontuação global de resiliência cultural (média por respondente)
        culture_scores = [calculate_mean(row) for row in item_matrix]
        
        # Simulação de métricas de sucesso de projeto correlacionadas com a cultura
        project_success_metrics = [
            score * 0.85 + random.uniform(-0.3, 0.3) for score in culture_scores
        ]
        
        # Correlação de Pearson
        corr = calculate_pearson_correlation(culture_scores, project_success_metrics)

        print(f"Estudo Piloto {pilot}:")
        print(f"  - Alfa de Cronbach: {alpha:.3f} (Meta: >= 0.80)")
        print(f"  - Validade Preditiva (Correlação): {corr:.3f} (Meta: >= 0.60)")
        
        if alpha < 0.80 or corr < 0.60:
            success_criteria_met = False

    print("\n-----------------------------------------------------------")
    if success_criteria_met:
        print("RESULTADO GLOBAL: APROVADO. Todos os estudos piloto atingiram os limiares estatísticos.")
    else:
        print("RESULTADO GLOBAL: REPROVADO. Limiares estatísticos não alcançados.")
    print("-----------------------------------------------------------")
    
    assert success_criteria_met, "O modelo falhou em atingir os critérios estatísticos de confiabilidade ou validade."

if __name__ == "__main__":
    run_validation()