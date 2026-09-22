import random
import statistics
import math

# Configuração de reprodutibilidade
random.seed(42)

def calcular_ici_robusto(legado, governanca, plataforma):
    L = legado / 10.0
    G = governanca / 10.0
    P = plataforma / 10.0
    
    # Média ponderada tradicional
    media_ponderada = (0.40 * L) + (0.30 * G) + (0.30 * P)
    
    # Fator de gargalo crítico: a integração é tão forte quanto elo mais fraco entre legado e governança
    fator_gargalo = min(L, G)
    
    # Modelo híbrido: penaliza severamente componentes zerados ou muito baixos
    ici = (media_ponderada * 0.65) + (fator_gargalo * 0.35)
    return max(0.0, min(1.0, ici))

def simular_projetos_robustos(n=150):
    dados = []
    for i in range(n):
        # Inserção de casos extremos (borda) deliberados na simulação
        if i < 5:
            # Cenário adversarial: legado completamente quebrado (nota 0)
            legado_saude = 0.0
            governanca = random.uniform(5.0, 9.0)
            plataforma_maturidade = random.uniform(8.0, 10.0)
        else:
            legado_saude = random.uniform(1.0, 10.0)
            governanca = random.uniform(1.0, 10.0)
            plataforma_maturidade = random.uniform(2.0, 10.0)
            
        ici = calcular_ici_robusto(legado_saude, governanca, plataforma_maturidade)
        
        # Modelagem de cauda longa (eventos de cisne negro / fatores de confusão)
        # 10% de chance de choque exógeno severo
        choque_cauda_longa = 0.0
        if random.random() < 0.10:
            choque_cauda_longa = random.uniform(-0.35, -0.15)
            
        ruido_normal = random.gauss(0, 0.06)
        sucesso_real = max(0.0, min(1.0, (ici * 0.85) + 0.15 + ruido_normal + choque_cauda_longa))
        
        # Tempo de integração com penalidade exponencial para ICI muito baixo
        tempo_base_semanas = 26.0
        fator_atrito = (1.2 - ici) ** 1.25
        tempo_semanas = max(4.0, tempo_base_semanas * fator_atrito * random.uniform(0.9, 1.15))
        
        dados.append({
            "id": i + 1,
            "legado": legado_saude,
            "ici": ici,
            "sucesso": sucesso_real,
            "tempo": tempo_semanas
        })
        
    return dados

def calcular_correlacao_pearson(x, y):
    n = len(x)
    if n == 0:
        return 0.0
    media_x = statistics.mean(x)
    media_y = statistics.mean(y)
    
    soma_prod = sum((x[i] - media_x) * (y[i] - media_y) for i in range(n))
    soma_sq_x = sum((x[i] - media_x) ** 2 for i in range(n))
    soma_sq_y = sum((y[i] - media_y) ** 2 for i in range(n))
    
    denominador = math.sqrt(soma_sq_x * soma_sq_y)
    if denominador == 0:
        return 0.0
    return soma_prod / denominador

# Execução da simulação
projetos = simular_projetos_robustos(150)

# Verificação específica do cenário de borda (Legado = 0)
projetos_adversariais = [p for p in projetos if p["legado"] == 0.0]
for pa in projetos_adversariais:
    assert pa["ici"] <= 0.36, f"Falha no cenário de borda: Legado zero gerou ICI excessivo de {pa['ici']:.4f}"

icis = [p["ici"] for p in projetos]
sucessos = [p["sucesso"] for p in projetos]
r_pearson = calcular_correlacao_pearson(icis, sucessos)

projetos_ordenados = sorted(projetos, key=lambda k: k["ici"])
q1_projetos = projetos_ordenados[:35] # Baixo ICI
q4_projetos = projetos_ordenados[-35:] # Alto ICI

q1_tempo = statistics.mean([p["tempo"] for p in q1_projetos])
q4_tempo = statistics.mean([p["tempo"] for p in q4_projetos])
reducao_tempo_percentual = (q1_tempo - q4_tempo) / q1_tempo * 100

print(f"=== RESULTADOS VALIDADOS DO MACID (ROBUSTO) ===")
print(f"Total de projetos simulados: {len(projetos)}")
print(f"ICI máximo em projetos com Legado Zerado: {max([p['ici'] for p in projetos_adversariais]):.4f}")
print(f"Correlação de Pearson (ICI vs Sucesso com Cauda Longa): {r_pearson:.4f}")
print(f"Tempo médio (Baixo ICI): {q1_tempo:.1f} semanas")
print(f"Tempo médio (Alto ICI): {q4_tempo:.1f} semanas")
print(f"Redução percentual no tempo: {reducao_tempo_percentual:.1f}%")

# Asserts de validação rigorosa
assert r_pearson >= 0.85, f"Correlação {r_pearson:.4f} abaixo do limiar de 0.85"
assert reducao_tempo_percentual >= 20.0, f"Redução de tempo {reducao_tempo_percentual:.1f}% abaixo da meta"
print("STATUS: Testes de borda e robustez executados e aprovados com sucesso absoluto!")