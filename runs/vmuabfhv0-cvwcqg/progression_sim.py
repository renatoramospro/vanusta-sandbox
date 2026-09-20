import math

def simulate_progression(levels, xp_growth_rate, power_growth_rate, xp_base, xp_per_min_base):
    """
    Simula a progressão de níveis.
    xp_growth_rate: taxa de crescimento do XP necessário (ex: 0.265 para 26.5%)
    power_growth_rate: taxa de crescimento da eficiência do jogador (ex: 0.10 para 10%)
    """
    results = []
    current_xp_req = xp_base
    current_xp_per_min = xp_per_min_base
    
    for n in range(levels):
        time_to_level = current_xp_req / current_xp_per_min
        results.append({
            "level": n,
            "xp_req": current_xp_req,
            "xp_per_min": current_xp_per_min,
            "time_to_level": time_to_level
        })
        
        # Preparar para o próximo nível
        current_xp_req *= (1 + xp_growth_rate)
        current_xp_per_min *= (1 + power_growth_rate)
        
    return results

def analyze_results(results):
    print(f"{'Nível':<6} | {'XP Req':<12} | {'XP/Min':<10} | {'Tempo (min)':<12} | {'Cresc. Tempo':<12}")
    print("-" * 65)
    for i in range(len(results)):
        row = results[i]
        growth_str = "-"
        if i > 0:
            growth = (results[i]["time_to_level"] / results[i-1]["time_to_level"]) - 1
            growth_str = f"{growth:.2%}"
        
        print(f"{row['level']:<6} | {row['xp_req']:<12.0f} | {row['xp_per_min']:<10.0f} | {row['time_to_level']:<12.2f} | {growth_str:<12}")

# Configurações
LEVELS = 6
XP_BASE = 1000
XP_MIN_BASE = 100
POWER_GROWTH = 0.10  # Jogador fica 10% mais forte/rápido por nível
TARGET_TIME_GROWTH = 0.15 # Queremos 15% de aumento no tempo

# 1. Cálculo do XP Growth necessário para o sucesso
# (1 + r_xp) = (1 + target_time_growth) * (1 + power_growth)
required_xp_growth = (1 + TARGET_TIME_GROWTH) * (1 + POWER_GROWTH) - 1

print("=== CENÁRIO 1: MODELO MATEMÁTICO CORRETO ===")
print(f"Taxa de XP necessária calculada: {required_xp_growth:.2%}\n")
correct_results = simulate_progression(LEVELS, required_xp_growth, POWER_GROWTH, XP_BASE, XP_MIN_BASE)
analyze_results(correct_results)

print("\n" + "="*65 + "\n")

print("=== CENÁRIO 2: EQUÍVOCO COMUM (Aumentar XP apenas em 15%) ===")
print("Erro: O designer esqueceu que o jogador fica mais forte.\n")
wrong_results = simulate_progression(LEVELS, TARGET_TIME_GROWTH, POWER_GROWTH, XP_BASE, XP_MIN_BASE)
analyze_results(wrong_results)

# Validação de Assert
last_growth_correct = (correct_results[-1]["time_to_level"] / correct_results[-2]["time_to_level"]) - 1
last_growth_wrong = (wrong_results[-1]["time_to_level"] / wrong_results[-2]["time_to_level"]) - 1

assert abs(last_growth_correct - TARGET_TIME_GROWTH) < 0.01, "O modelo correto falhou em atingir a meta de 15%!"
assert last_growth_wrong < TARGET_TIME_GROWTH, "O modelo errado deveria ter crescido menos que 15%!"

print("\n[VEREDITO] Experimento concluído com sucesso: As curvas foram validadas.")