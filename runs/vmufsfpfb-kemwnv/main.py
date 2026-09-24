import uuid
import time
from functools import wraps

# Cache de idempotência
cache = {}

def idempotent(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Gerar chave
        chave = str(uuid.uuid4())
        
        # Armazenar chave
        cache[chave] = None
        
        # Processar requisição
        resultado = func(*args, **kwargs)
        
        # Atualizar cache
        cache[chave] = resultado
        
        # Verificar requisições subsequentes
        while True:
            # Verificar se há requisições subsequentes com a mesma chave
            if chave in cache and cache[chave] is not None:
                # Retornar resultado cacheado
                return cache[chave]
            # Aguardar por 1 segundo
            time.sleep(1)
    
    return wrapper

# Exemplo de função idempotente
@idempotent
def criar_recurso(nome):
    # Processar requisição
    print(f"Criando recurso {nome}")
    time.sleep(2)  # Simulando tempo de processamento
    return f"Recurso {nome} criado com sucesso"

# Testar a função idempotente
print(criar_recurso("Recurso 1"))  # Criar recurso 1
print(criar_recurso("Recurso 1"))  # Requisição subsequente com a mesma chave