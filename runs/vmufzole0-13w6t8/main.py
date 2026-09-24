import asyncio
import json

# --- BANCO DE DADOS SIMULADO ---
DB_EXHIBITIONS = [
    {"id": "ex-1", "title": "Art Exhibition 1", "organizer_id": "org-17"},
    {"id": "ex-2", "title": "Art Exhibition 2", "organizer_id": "org-17"},
    {"id": "ex-3", "title": "Art Exhibition 3", "organizer_id": "org-17"},
]

DB_TICKETS = [
    {"id": "t-1", "exhibition_id": "ex-1", "seat": "A1", "price": 100},
    {"id": "t-2", "exhibition_id": "ex-1", "seat": "A2", "price": 100},
    {"id": "t-3", "exhibition_id": "ex-2", "seat": "B1", "price": 150},
    # ex-3 não possui tickets
]

# Contador global de queries simuladas para auditoria de performance
query_counter = {
    "exhibitions": 0,
    "tickets": 0
}

def reset_query_counter():
    query_counter["exhibitions"] = 0
    query_counter["tickets"] = 0

# --- IMPLEMENTAÇÃO DO DATALOADER ---
class DataLoader:
    """
    Implementação robusta do padrão DataLoader em Python.
    Garante batching (agrupamento) e caching por ciclo de vida da requisição.
    """
    def __init__(self, batch_load_fn):
        self.batch_load_fn = batch_load_fn
        self._keys = []
        self._futures = {}
        self._cache = {}
        self._dispatch_task = None

    async def load(self, key):
        # Retorna do cache se já estiver carregado nesta requisição
        if key in self._cache:
            return self._cache[key]
        
        # Cria um Future para a chave se ela ainda não estiver sendo carregada
        if key not in self._futures:
            self._futures[key] = asyncio.get_running_loop().create_future()
            self._keys.append(key)
            
        # Agenda o despacho do lote para o próximo ciclo do event loop
        if not self._dispatch_task:
            self._dispatch_task = asyncio.create_task(self._dispatch())
            
        return await self._futures[key]

    async def _dispatch(self):
        # Cede o controle para permitir que outras chamadas concorrentes acumulem suas chaves
        await asyncio.sleep(0)
        
        keys_to_load = list(self._keys)
        self._keys = []
        self._dispatch_task = None
        
        if not keys_to_load:
            return
            
        try:
            # Executa a função de lote
            results = await self.batch_load_fn(keys_to_load)
            
            # Garante que o tamanho do resultado corresponda ao tamanho das chaves
            if len(results) != len(keys_to_load):
                raise ValueError("A função de lote deve retornar um array de mesmo tamanho que o de chaves.")
                
            for key, result in zip(keys_to_load, results):
                self._cache[key] = result
                future = self._futures.pop(key, None)
                if future and not future.done():
                    future.set_result(result)
        except Exception as e:
            for key in keys_to_load:
                future = self._futures.pop(key, None)
                if future and not future.done():
                    future.set_exception(e)

# --- CONTEXTO DA REQUISIÇÃO ---
class RequestContext:
    """
    Representa o contexto de uma única requisição GraphQL.
    Garante o isolamento de cache e autorização por usuário.
    """
    def __init__(self, user_role="user", allowed_exhibitions=None):
        self.user_role = user_role
        self.allowed_exhibitions = allowed_exhibitions  # None significa acesso total (ex: admin)
        # O DataLoader é instanciado por requisição!
        self.tickets_loader = DataLoader(lambda keys: batch_load_tickets(keys, self))

# --- FUNÇÃO DE LOTE (BATCH LOAD FUNCTION) ---
async def batch_load_tickets(exhibition_ids, context):
    """
    Busca os tickets para múltiplas exposições em uma única query simulada.
    Aplica ordenação estrita e regras de autorização no lote.
    """
    query_counter["tickets"] += 1
    
    # Simula query em lote (ex: SELECT * FROM tickets WHERE exhibition_id IN (...))
    all_tickets = [t for t in DB_TICKETS if t["exhibition_id"] in exhibition_ids]
    
    # Aplica autorização no lote: filtra tickets de exposições não permitidas
    if context.allowed_exhibitions is not None:
        all_tickets = [t for t in all_tickets if t["exhibition_id"] in context.allowed_exhibitions]
        
    # Agrupa os resultados por exhibition_id
    tickets_by_exhibition = {}
    for t in all_tickets:
        eid = t["exhibition_id"]
        if eid not in tickets_by_exhibition:
            tickets_by_exhibition[eid] = []
        tickets_by_exhibition[eid].append(t)
        
    # Constrói o resultado garantindo a ordenação estrita correspondente às chaves de entrada.
    # Se uma exposição não tiver tickets ou não for permitida, retorna uma lista vazia [].
    # Isso respeita o tipo GraphQL [Ticket!]! que não pode ser nulo mas pode ser vazio.
    ordered_results = []
    for eid in exhibition_ids:
        ordered_results.append(tickets_by_exhibition.get(eid, []))
        
    return ordered_results

# --- RESOLVERS GRAPHQL SIMULADOS ---
async def resolve_tickets(exhibition_id, context):
    return await context.tickets_loader.load(exhibition_id)

async def resolve_exhibitions_by_organizer(organizer_id, context):
    query_counter["exhibitions"] += 1
    # Simula busca de exposições por organizador
    exhibitions = [ex for ex in DB_EXHIBITIONS if ex["organizer_id"] == organizer_id]
    
    # Resolve os tickets concorrentemente para cada exposição
    tasks = []
    for ex in exhibitions:
        async def resolve_ex(e):
            tickets = await resolve_tickets(e["id"], context)
            return {**e, "tickets": tickets}
        tasks.append(resolve_ex(ex))
        
    return await asyncio.gather(*tasks)

async def execute_graphql_query(organizer_id, context):
    """Simula a execução de uma query GraphQL."""
    exhibitions = await resolve_exhibitions_by_organizer(organizer_id, context)
    return {"exhibitionsByOrganizer": exhibitions}

# --- SUITE DE TESTES ---
async def run_tests():
    print("=== INICIANDO TESTES DO DATALOADER ===")

    # -------------------------------------------------------------------------
    # CENÁRIO 1: Batching um-para-muitos (Resolução do problema N+1)
    # -------------------------------------------------------------------------
    reset_query_counter()
    context = RequestContext(user_role="admin") # Admin tem acesso a tudo
    
    result = await execute_graphql_query("org-17", context)
    
    print("\nCenário 1 - Resultado da Query:")
    print(json.dumps(result, indent=2))
    
    print(f"Queries de Exposições: {query_counter['exhibitions']}")
    print(f"Queries de Tickets: {query_counter['tickets']}")
    
    # Asserções de performance
    assert query_counter["exhibitions"] == 1, "Deveria ter feito apenas 1 query para exposições"
    assert query_counter["tickets"] == 1, f"Deveria ter feito apenas 1 query para tickets (Batching falhou! Fez {query_counter['tickets']})"
    print("-> Cenário 1 passou com sucesso! Batching reduziu as consultas de N+1 para exatamente 2.")

    # -------------------------------------------------------------------------
    # CENÁRIO 2: Ordenação estrita, chaves ausentes e repetidas
    # -------------------------------------------------------------------------
    reset_query_counter()
    context_scenario_2 = RequestContext(user_role="admin")
    
    # Carrega chaves de forma desordenada, repetida e com chave inexistente/sem tickets
    keys = ["ex-2", "ex-1", "ex-3", "ex-2"]
    tasks = [context_scenario_2.tickets_loader.load(k) for k in keys]
    results = await asyncio.gather(*tasks)
    
    print("\nCenário 2 - Ordenação e Deduplicação:")
    print(f"Chaves solicitadas: {keys}")
    print(f"Queries de Tickets realizadas: {query_counter['tickets']}")
    
    # Deve fazer apenas 1 query para carregar tudo devido à deduplicação e batching
    assert query_counter["tickets"] == 1, f"Deveria ter feito apenas 1 query para tickets no Cenário 2. Fez {query_counter['tickets']}"
    
    # Verifica se os resultados correspondem exatamente às chaves na mesma ordem
    # ex-2 tem ticket t-3
    assert results[0][0]["id"] == "t-3"
    # ex-1 tem tickets t-1 e t-2
    assert len(results[1]) == 2
    # ex-3 não tem tickets (deve retornar lista vazia [])
    assert results[2] == []
    # ex-2 repetido deve retornar o mesmo resultado do primeiro ex-2 (cache)
    assert results[3] == results[0]
    print("-> Cenário 2 passou com sucesso! Ordenação estrita, chaves ausentes e deduplicação validadas.")

    # -------------------------------------------------------------------------
    # CENÁRIO 3: Isolamento entre requisições concorrentes (Evitar Data Leak)
    # -------------------------------------------------------------------------
    reset_query_counter()
    
    # Requisição do Usuário A (só pode ver ex-1)
    context_user_a = RequestContext(user_role="user", allowed_exhibitions=["ex-1"])
    # Requisição do Usuário B (só pode ver ex-2)
    context_user_b = RequestContext(user_role="user", allowed_exhibitions=["ex-2"])
    
    # Executamos concorrentemente para simular requisições HTTP paralelas
    res_a, res_b = await asyncio.gather(
        execute_graphql_query("org-17", context_user_a),
        execute_graphql_query("org-17", context_user_b)
    )
    
    print("\nCenário 3 - Isolamento de Cache e Autorização Concorrente:")
    print("Resultado Usuário A (Permissão apenas para ex-1):")
    for ex in res_a["exhibitionsByOrganizer"]:
        print(f"  Exposição {ex['id']}: {len(ex['tickets'])} tickets")
        if ex["id"] == "ex-2":
            assert len(ex["tickets"]) == 0, "Usuário A não deveria ver tickets de ex-2!"
            
    print("Resultado Usuário B (Permissão apenas para ex-2):")
    for ex in res_b["exhibitionsByOrganizer"]:
        print(f"  Exposição {ex['id']}: {len(ex['tickets'])} tickets")
        if ex["id"] == "ex-1":
            assert len(ex["tickets"]) == 0, "Usuário B não deveria ver tickets de ex-1!"

    print("\n=== TODOS OS TESTES PASSARAM COM SUCESSO! ===")

if __name__ == "__main__":
    asyncio.run(run_tests())