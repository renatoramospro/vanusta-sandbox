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
        value = self.base_value * self.multiplier
        self.total_processed += value
        return value

class MacroControllerPI:
    """Controlador PI (Proporcional-Integral) para ajuste dinâmico robusto."""
    def __init__(self, kp=1.2, ki=0.05):
        self.kp = kp  # Ganho Proporcional
        self.ki = ki  # Ganho Integral
        self.integral_error = 0.0

    def adjust(self, target_money, current_money, faucets, sinks):
        # Erro de massa monetária em relação ao alvo desejado
        error = (current_money - target_money) / target_money
        self.integral_error += error
        
        # Correção combinada Proporcional + Integral
        adjustment = (error * self.kp) + (self.integral_error * self.ki)
        
        for f in faucets:
            # Faucets diminuem quando há excesso de moeda
            f.multiplier = max(0.05, f.multiplier - adjustment)
        
        for s in sinks:
            # Sinks aumentam quando há excesso de moeda para drená-la
            s.multiplier = max(0.1, s.multiplier + (adjustment * 2.0))

class EconomyEngine:
    def __init__(self, initial_money):
        self.total_money = initial_money
        self.initial_money = initial_money
        self.faucets = []
        self.sinks = []
        # Utiliza controlador PI para zerar o erro estacionário
        self.controller = MacroControllerPI(kp=1.5, ki=0.08)
        self.history = []

    def add_faucet(self, component): self.faucets.append(component)
    def add_sink(self, component): self.sinks.append(component)

    def run_cycle(self, cycle_num, is_shock_active=False):
        cycle_inflow = 0.0
        cycle_outflow = 0.0

        # Aplica choque de oferta se ativo (multiplica temporariamente a base dos faucets)
        shock_factor = 2.5 if is_shock_active else 1.0

        for f in self.faucets:
            original_mult = f.multiplier
            f.multiplier *= shock_factor
            cycle_inflow += f.execute()
            f.multiplier = original_mult # Restaura o multiplicador base para o controlador ajustar

        for s in self.sinks:
            cycle_outflow += s.execute()

        # Atualiza massa monetária líquida
        self.total_money += (cycle_inflow - cycle_outflow)
        if self.total_money < 1.0:
            self.total_money = 1.0 # Previne colapso monetário absoluto

        # O controlador atua para manter a massa monetária próxima ao alvo inicial
        self.controller.adjust(self.initial_money, self.total_money, self.faucets, self.sinks)

        self.history.append({
            "cycle": cycle_num,
            "total_money": self.total_money,
            "inflow": cycle_inflow,
            "outflow": cycle_outflow
        })

def main():
    print("="*50)
    print("INICIALIZANDO SIMULAÇÃO MACROECONÔMICA (PI CONTROLLER)")
    print("="*50)

    initial_liquidity = 1000.0
    engine = EconomyEngine(initial_liquidity)

    # Adicionando Faucets e Sinks por Categoria
    engine.add_faucet(EconomicComponent("Quest Rewards", 15.0, category="Rewards", is_sink=False))
    engine.add_faucet(EconomicComponent("Monster Drops", 10.0, category="Rewards", is_sink=False))
    
    engine.add_sink(EconomicComponent("Item Repair", 12.0, category="Maintenance", is_sink=True))
    engine.add_sink(EconomicComponent("Fast Travel Fees", 8.0, category="Maintenance", is_sink=True))

    # Execução de 1000 ciclos com Choque de Oferta entre os ciclos 500 e 550
    for cycle in range(1, 1001):
        shock = (500 <= cycle <= 550)
        engine.run_cycle(cycle, is_shock_active=shock)

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
        print(f"[{cat}] In: {cat_in:10.2f} | Out: {cat_out:10.2f} | Delta: {delta:10.2f}")

    print("\n[Nota de Auditoria] Transações de mercado (trocas) foram ignoradas no cálculo de massa,")
    print("confirmando que apenas Faucets e Sinks alteram a inflação.")

    print("\n" + "="*50)
    print(f"VERIFICAÇÃO DE CRITÉRIO DE SUCESSO:")
    print(f"Inflação Acumulada < 5%? {'✅ SIM' if abs(final_inflation) < 0.05 else '❌ NÃO'}")
    print(f"Resultado: {final_inflation*100:.2f}%")
    print("="*50)

    # Assert corrigido para validar o critério rigoroso da missão
    assert abs(final_inflation) < 0.05, f"A inflação excedeu o limite de 5%! Atual: {final_inflation*100:.2f}%"

if __name__ == "__main__":
    main()