import math

class EconomicComponent:
    def __init__(self, name, base_value, category, is_sink=False):
        self.name = name
        self.base_value = base_value
        self.multiplier = 1.0
        self.category = category
        self.is_sink = is_sink
        self.total_processed = 0.0

    def execute(self):
        # O valor processado é o que entra ou sai do sistema
        value = self.base_value * self.multiplier
        self.total_processed += value
        return value

class AdaptiveMacroController:
    """
    Controlador de Ganho Adaptativo (Gain Scheduling).
    Aumenta a agressividade do ajuste conforme o erro de inflação cresce.
    """
    def __init__(self, target_inflation=0.0, kp_base=0.2, ki=0.05):
        self.target_inflation = target_inflation
        self.kp_base = kp_base
        self.ki = ki
        self.integral_error = 0.0

    def adjust(self, current_inflation, faucets, sinks):
        error = current_inflation - self.target_inflation
        
        # Anti-windup: limita o acúmulo do erro integral para evitar overshoot massivo
        self.integral_error = max(-1.0, min(1.0, self.integral_error + error))
        
        # Gain Scheduling: Se a inflação subir muito, o ganho proporcional aumenta exponencialmente
        # Isso permite uma resposta rápida a choques (como o do ciclo 500)
        kp_adaptive = self.kp_base * (1.0 + abs(error) * 10.0)
        
        adjustment = (error * kp_adaptive) + (self.integral_error * self.ki)
        
        # Se inflação > alvo (error > 0), precisamos diminuir Faucets e aumentar Sinks
        # Se inflação < alvo (error < 0), precisamos aumentar Faucets e diminuir Sinks
        for f in faucets:
            # Reduz multiplicador se inflação alta, aumenta se baixa
            f.multiplier = max(0.1, f.multiplier - adjustment)
            
        for s in sinks:
            # Aumenta multiplicador se inflação alta, reduz se baixa
            s.multiplier = max(0.1, s.multiplier + adjustment)

class EconomyEngine:
    def __init__(self, initial_liquidity):
        self.total_money = initial_liquidity
        self.initial_liquidity = initial_liquidity
        self.faucets = []
        self.sinks = []
        self.controller = AdaptiveMacroController()

    def run_cycle(self, cycle, is_shock_active=False):
        cycle_in = 0.0
        cycle_out = 0.0

        # 1. Aplicar Choque de Oferta (ex: evento de loot massivo)
        shock_multiplier = 15.0 if is_shock_active else 1.0

        # 2. Executar Faucets (Geração)
        for f in self.faucets:
            val = f.execute()
            if f.name == "Quest Rewards" and is_shock_active:
                val *= shock_multiplier
            cycle_in += val

        # 3. Executar Sinks (Destruição)
        for s in self.sinks:
            val = s.execute()
            cycle_out += val

        # 4. Atualizar Massa Monetária
        self.total_money += (cycle_in - cycle_out)
        
        # 5. Calcular Inflação Atual (baseada na massa monetária)
        current_inflation = (self.total_money - self.initial_liquidity) / self.initial_liquidity
        
        # 6. Ajustar parâmetros para o próximo ciclo
        self.controller.adjust(current_inflation, self.faucets, self.sinks)

def main():
    print("="*50)
    print("INICIALIZANDO SIMULAÇÃO MACROECONÔMICA (ADAPTIVE GAIN)")
    print("="*50)

    initial_liquidity = 1000.0
    engine = EconomyEngine(initial_liquidity)

    # Configuração de Componentes
    engine.faucets.append(EconomicComponent("Quest Rewards", 10.0, "Rewards"))
    engine.faucets.append(EconomicComponent("Monster Loot", 5.0, "Rewards"))
    
    engine.sinks.append(EconomicComponent("Maintenance", 12.0, "Maintenance", is_sink=True))
    engine.sinks.append(EconomicComponent("Market Tax", 3.0, "Tax", is_sink=True))

    total_cycles = 1000
    shock_start = 500
    shock_end = 550

    for cycle in range(1, total_cycles + 1):
        is_shock = shock_start <= cycle <= shock_end
        engine.run_cycle(cycle, is_shock_active=is_shock)

    # Relatório Final
    final_money = engine.total_money
    final_inflation = (final_money - initial_liquidity) / initial_liquidity

    print("\n" + "="*50)
    print("RELATÓRIO DE BALANÇO DE LIQUIDEZ E MACROECONOMIA")
    print("="*50)
    print(f"Massa Monetária Inicial: {initial_liquidity:.2f}")
    print(f"Massa Monetária Final:   {final_money:.2f}")
    print(f"Inflação Acumulada:      {final_inflation*100:.2f}%")
    print("\n--- Balanço por Categoria ---")
    
    categories = set(f.category for f in engine.faucets).union(set(s.category for s in engine.sinks))
    for cat in sorted(categories):
        cat_in = sum(f.total_processed for f in engine.faucets if f.category == cat)
        cat_out = sum(s.total_processed for s in engine.sinks if s.category == cat)
        delta = cat_in - cat_out
        print(f"[{cat:12}] In: {cat_in:10.2f} | Out: {cat_out:10.2f} | Delta: {delta:10.2f}")

    print("\n" + "="*50)
    print(f"VERIFICAÇÃO DE CRITÉRIO DE SUCESSO:")
    success = abs(final_inflation) < 0.05
    print(f"Inflação Acumulada < 5%? {'✅ SIM' if success else '❌ NÃO'}")
    print(f"Resultado: {final_inflation*100:.2f}%")
    print("="*50)

    # Segurança: Uso de RuntimeError em vez de assert para regras de negócio
    if not success:
        raise RuntimeError(f"FALHA CRÍTICA DE CONTROLE: Inflação de {final_inflation*100:.2f}% excedeu o limite de 5%!")

if __name__ == "__main__":
    main()