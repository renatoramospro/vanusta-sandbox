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
    # ex-3 não tem tickets
]

# Contador de queries simuladas para auditoria de performance
query_counter = {
    "exhibitions": 0,
    "tickets": 0
}

def reset_query_counter():
    query_counter["exhibitions"] = 0
    query_counter["tickets"] = 0

# --- IMPLEMENTAÇÃO DO DATALOADER ---
class DataLoader:
    def __init__(self, batch_load_fn):
        self.batch_load_fn = batch_load_fn
        self._keys = []
        self._promises = {}
        self._cache = {}
        self._batch_task = None

    async def load(self, key):
        # Cache por requisição: se a mesma chave for pedida na mesma requisição, retorna do cache
        if key in self._cache:
            return self._cache[key]
        
        if key not in self._promises:
            self._promises[key] = asyncio.get_running_loop().create_future()
            self._keys.append(key)
            
            if not self._batch_task:
                # Agenda o dispatch para a próxima iteração do event loop (microtask/tick)
                self._batch_task = asyncio.create_task(self._dispatch())
                
        return await self._promises[key]

    async def _dispatch(self):
        # Cede controle para permitir que outras chamadas .load() na mesma iteração acumulem chaves
        await asyncio.sleep(0)
        
        keys_to_load = list(self._keys)
        promises_to_resolve = dict(self._promises)
        
        # Reseta o estado para o próximo lote
        self._keys = []
        self._promises = {}
        self._batch_task = None
        
        if not keys_to_load:
            return

        try:
            results = await self.batch_load_fn(keys_to_load)
            
            # Garante que o número de resultados corresponde ao número de chaves
            if len(results) != len(keys_to_load):
                raise ValueError(f"O tamanho do resultado ({len(results)}) difere do tamanho das chaves ({len(keys_to_load)})")
                
            for key, result in zip(keys_to_load, results):
                self._cache[key] = result
                promises_to_resolve[key].set_result(result)
        except Exception as e:
            for key in keys_to_load:
                promises_to_resolve[key].set_exception(e)


# --- CONTEXTO DA REQUISIÇÃO ---
class RequestContext:
    def __init__(self, user_role, allowed_exhibitions=None):
        self.user_role = user_role
        self.allowed_exhibitions = allowed_exhibitions or []
        # DataLoader instanciado por requisição para garantir isolamento de cache!
        self.tickets_loader = DataLoader(self.batch_load_tickets)

    async def batch_load_tickets(self, exhibition_ids):
        query_counter["tickets"] += 1
        
        # Simula a query SQL: SELECT * FROM tickets WHERE exhibition_id IN (...)
        fetched_tickets = [t for t in DB_TICKETS if t["exhibition_id"] in exhibition_ids]
        
        # Aplicação de Autorização no Lote (Segurança)
        if self.user_role != "admin":
            fetched_tickets = [t for t in fetched_tickets if t["exhibition_id"] in self.allowed_exhibitions]

        # Mapeamento para garantir a ORDENAÇÃO estrita e tratamento de chaves ausentes
        tickets_by_exhibition = {ex_id: [] for ex_id in exhibition_ids}
        for ticket in fetched_tickets:
            tickets_by_exhibition[ticket["exhibition_id"]].append(ticket)
            
        return [tickets_by_exhibition[ex_id] for ex_id in exhibition_ids]


# --- SIMULAÇÃO DO GRAPHQL ENGINE ---
async def resolve_exhibitions_by_organizer(organizer_id):
    query_counter["exhibitions"] += 1
    return [ex for ex in DB_EXHIBITIONS if ex["organizer_id"] == organizer_id]

async def resolve_exhibition_tickets(exhibition, context: RequestContext):
    return await context.tickets_loader.load(exhibition["id"])

async def execute_graphql_query(organizer_id, context: RequestContext):
    # 1. Resolve a query raiz (busca exposições)
    exhibitions = await resolve_exhibitions_by_organizer(organizer_id)
    
    # 2. Resolve os campos filhos (tickets) concorrentemente, simulando o comportamento do GraphQL
    tasks = []
    for ex in exhibitions:
        async def resolve_and_bind(e):
            tickets = await resolve_exhibition_tickets(e, context)
            return {**e, "tickets": tickets}
        tasks.append(resolve_and_bind(ex))
        
    resolved_exhibitions = await asyncio.gather(*tasks)
    return {"exhibitionsByOrganizer": resolved_exhibitions}


# --- EXECUÇÃO DOS TESTES ---
async def run_tests():
    print("=== INICIANDO TESTES DO DATALOADER ===")

    # -------------------------------------------------------------------------
    # CENÁRIO 1: Batching Um-para-Muitos (Redução de N+1 para exatamente 2 queries)
    # -------------------------------------------------------------------------
    reset_query_counter()
    context_admin = RequestContext(user_role="admin", allowed_exhibitions=["ex-1", "ex-2", "ex-3"])
    
    result = await execute_graphql_query("org-17", context_admin)
    
    print("\nCenário 1 - Resultado da Query:")
    print(json.dumps(result, indent=2))
    
    print(f"Queries de Exhibitions: {query_counter['exhibitions']}")
    print(f"Queries de Tickets: {query_counter['tickets']}")
    
    assert query_counter["exhibitions"] == 1, "Deveria fazer exatamente 1 query de exhibitions"
    assert query_counter["tickets"] == 1, "Deveria fazer exatamente 1 query de tickets (batching funcionou!)"
    assert len(result["exhibitionsByOrganizer"]) == 3
    
    # -------------------------------------------------------------------------
    # CENÁRIO 2: Ordenação com chaves ausentes e repetidas
    # -------------------------------------------------------------------------
    reset_query_counter()
    loader = context_admin.tickets_loader
    
    # Carregamos chaves em ordem específica, incluindo repetidas e uma inexistente/sem tickets (ex-3)
    t3, t1_a, t2, t1_b = await asyncio.gather(
        loader.load("ex-3"),
        loader.load("ex-1"),
        loader.load("ex-2"),
        loader.load("ex-1")  # Chave repetida (deve usar cache)
    )
    
    print("\nCenário 2 - Ordenação e Chaves Ausentes/Repetidas:")
    print(f"Tickets ex-3 (ausente/vazio): {t3}")
    print(f"Tickets ex-1 (primeira chamada): {t1_a}")
    print(f"Tickets ex-2: {t2}")
    print(f"Tickets ex-1 (segunda chamada - cache): {t1_b}")
    
    assert t3 == [], "ex-3 deveria retornar lista vazia"
    assert len(t1_a) == 2, "ex-1 deveria ter 2 tickets"
    assert len(t2) == 1, "ex-2 deveria ter 1 ticket"
    assert t1_a is t1_b, "A segunda chamada para ex-1 deveria retornar exatamente a mesma instância do cache"
    assert query_counter["tickets"] == 1, "Deveria ter feito apenas 1 query para carregar tudo"

    # -------------------------------------------------------------------------
    # CENÁRIO 3: Isolamento entre requisições concorrentes (Evitar Data Leak)
    # -------------------------------------------------------------------------
    reset_query_counter()
    
    # Requisição do Usuário A (só pode ver ex-1)
    context_user_a = RequestContext(user_role="user", allowed_exhibitions=["ex-1"])
    # Requisição do Usuário B (só pode ver ex-2)
    context_user_b = RequestContext(user_role="user", allowed_exhibitions=["ex-2"])
    
    # Executamos concorrentemente
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