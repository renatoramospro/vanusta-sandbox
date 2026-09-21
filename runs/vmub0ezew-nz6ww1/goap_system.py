import heapq
import time

class Action:
    def __init__(self, name, preconditions, effects, cost=1):
        self.name = name
        self.preconditions = preconditions  # dict: {"has_weapon": False}
        self.effects = effects              # dict: {"has_weapon": True}
        self.cost = cost

    def __repr__(self):
        return f"Action({self.name})"

class Planner:
    def plan(self, start_state, goal_state, actions):
        # Implementação de A* para busca no espaço de estados
        # O estado é tratado como um frozenset de itens para ser hashable
        start_state_tuple = frozenset(start_state.items())
        
        # priority_queue: (custo_total, estado_atual, caminho_de_acoes)
        queue = [(0, start_state_tuple, [])]
        visited = {start_state_tuple: 0}

        while queue:
            (cost, current_state_tuple, path) = heapq.heappop(queue)
            current_state = dict(current_state_tuple)

            # Verifica se o objetivo foi atingido (o objetivo é um subconjunto do estado)
            if all(current_state.get(k) == v for k, v in goal_state.items()):
                return path

            for action in actions:
                # Verifica se as precondições da ação são satisfeitas pelo estado atual
                if all(current_state.get(k) == v for k, v in action.preconditions.items()):
                    # Calcula o novo estado aplicando os efeitos
                    new_state = current_state.copy()
                    new_state.update(action.effects)
                    new_state_tuple = frozenset(new_state.items())

                    new_cost = cost + action.cost
                    if new_state_tuple not in visited or new_cost < visited[new_state_tuple]:
                        visited[new_state_tuple] = new_cost
                        heapq.heappush(queue, (new_cost, new_state_tuple, path + [action]))
        
        return None # Nenhum plano encontrado

class Agent:
    def __init__(self, name, actions):
        self.name = name
        self.actions = actions
        self.planner = Planner()
        self.world_state = {}
        self.goal = {}
        self.current_plan = []

    def update_world(self, new_state):
        self.world_state.update(new_state)

    def set_goal(self, goal):
        self.goal = goal
        self.current_plan = []

    def tick(self):
        # 1. Verifica se o plano atual ainda é válido (Resiliência)
        if self.current_plan:
            next_action = self.current_plan[0]
            # Se o mundo mudou e as precondições da próxima ação não são mais atendidas, o plano quebrou
            if not all(self.world_state.get(k) == v for k, v in next_action.preconditions.items()):
                print(f"[{self.name}] Plano inválido! O mundo mudou. Replanejando...")
                self.current_plan = []

        # 2. Se não há plano, tenta criar um
        if not self.current_plan:
            start_time = time.perf_counter()
            self.current_plan = self.planner.plan(self.world_state, self.goal, self.actions)
            end_time = time.perf_counter()
            
            if self.current_plan:
                print(f"[{self.name}] Novo plano encontrado em {(end_time - start_time)*1000:.4f}ms: {self.current_plan}")
            else:
                print(f"[{self.name}] Falha ao encontrar plano para o objetivo {self.goal}")
                return False

        # 3. Executa a próxima ação do plano
        action = self.current_plan.pop(0)
        print(f"[{self.name}] Executando: {action.name}")
        # Aplica os efeitos da ação ao mundo (simulação de execução)
        self.world_state.update(action.effects)
        return True

def run_simulation():
    # Definição de Ações
    actions = [
        Action("PegarArmaNoChao", {"has_weapon": False}, {"has_weapon": True}, cost=1),
        Action("ComprarArma", {"has_money": True}, {"has_weapon": True}, cost=5),
        Action("Atirar", {"has_weapon": True}, {"enemy_dead": True}, cost=1),
        Action("TrabalharParaGanharDinheiro", {"has_money": False}, {"has_money": True}, cost=10)
    ]

    agent = Agent("NPC_Soldado", actions)

    print("--- CENÁRIO 1: Caminho mais barato (Pegar arma no chão) ---")
    agent.update_world({"has_weapon": False, "has_money": False, "enemy_dead": False})
    agent.set_goal({"enemy_dead": True})
    
    while agent.tick() and not all(agent.world_state.get(k) == v for k, v in agent.goal.items()):
        pass

    print("\n--- CENÁRIO 2: Resiliência (Arma é roubada durante o processo) ---")
    # Reset
    agent.update_world({"has_weapon": False, "has_money": True, "enemy_dead": False})
    agent.set_goal({"enemy_dead": True})
    
    # Primeiro passo: Ele planeja e executa "ComprarArma" (porque não tem arma no chão no estado inicial deste cenário)
    # Mas vamos simular que ele pegou uma arma e ela sumiu
    agent.current_plan = [Action("PegarArmaNoChao", {}, {}, 1), Action("Atirar", {}, {}, 1)]
    agent.world_state = {"has_weapon": True, "has_money": True, "enemy_dead": False}
    
    print(f"Estado Inicial: {agent.world_state}")
    print(f"Plano Atual: {agent.current_plan}")
    
    # Simula o agente executando a primeira ação (Pegar arma)
    agent.tick() 
    
    # EVENTO EXTERNO: A arma sumiu!
    print("!!! EVENTO EXTERNO: Alguém roubou a arma do NPC !!!")
    agent.update_world({"has_weapon": False})
    
    # Próximo tick deve detectar a invalidez e replanejar para "ComprarArma"
    agent.tick() # Detecta e replaneja
    agent.tick() # Executa o novo plano (Comprar)
    agent.tick() # Executa o novo plano (Atirar)

if __name__ == "__main__":
    run_simulation()