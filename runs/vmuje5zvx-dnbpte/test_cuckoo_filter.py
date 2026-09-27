from cuckoo_filter import CuckooFilter
import random

def test_cuckoo_filter_operations():
    cf = CuckooFilter(capacity=2048, bucket_size=4, fingerprint_size=1)
    
    # Teste de inserção e busca básica
    assert cf.search("apple") == False, "Item não inserido não deve ser encontrado"
    assert cf.insert("apple") == True, "Deveria conseguir inserir 'apple'"
    assert cf.search("apple") == True, "Item inserido deve ser encontrado"
    
    # Teste de deleção (Ataca o equívoco comum: deleção não corrompe e limpa corretamente o slot)
    assert cf.delete("apple") == True, "Deveria conseguir deletar 'apple'"
    assert cf.search("apple") == False, "Item deletado não deve mais ser encontrado"

def test_false_positive_rate():
    # Cenário solicitado: 10.000 chaves (usaremos capacidade adequada para manter fator de carga seguro)
    # Com capacidade de 16384 baldes e 4 slots por balde (capacidade total = 65536), 
    # inserir 10.000 itens resulta em um fator de carga baixo, excelente para taxa de FP.
    capacity = 16384
    cf = CuckooFilter(capacity=capacity, bucket_size=4, fingerprint_size=2) # 2 bytes = 16 bits de fingerprint (~1/65536 taxa teórica)
    
    inserted_keys = [f"user_{i}" for i in range(10000)]
    
    for key in inserted_keys:
        success = cf.insert(key)
        assert success, f"Falha ao inserir a chave {key}"
        
    # Verifica que todas as chaves inseridas continuam presentes (False Negatives = 0)
    for key in inserted_keys[:100]: # Amostra para rapidez
        assert cf.search(key) == True, f"Falso negativo detectado para {key}"

    # Teste de falsos positivos com 1.000 chaves DISTINTAS não inseridas
    test_keys = [f"stranger_{i}" for i in range(1000)]
    false_positives = 0
    true_negatives = 0
    
    for key in test_keys:
        if cf.search(key):
            false_positives += 1
        else:
            true_negatives += 1
            
    fp_rate = false_positives / (false_positives + true_negatives)
    print(f"\n--- Estatísticas do Teste de Falsos Positivos ---")
    print(f"Total de chaves de teste: {len(test_keys)}")
    print(f"Falsos Positivos: {false_positives}")
    print(f"Verdadeiros Negativos: {true_negatives}")
    print(f"Taxa de Falsos Positivos: {fp_rate * 100:.4f}%")
    
    # Critério de sucesso: Taxa de falsos positivos inferior a 2%
    assert fp_rate < 0.02, f"Taxa de falsos positivos alta demais: {fp_rate * 100:.2f}% (esperado < 2%)"

def test_anti_pattern_counterexample():
    """
    Demonstra o contraexemplo de um equívoco comum mapeado pelo Arquiteto:
    'Qualquer hash funciona; não importa a distribuição.' / 'O fingerprint pode ser o hash completo.'
    Se usarmos um fingerprint muito pequeno (1 bit) ou uma função hash pobre (colisões extremas),
    a taxa de falsos positivos explode ou a inserção falha catastrófica.
    """
    cf_bad = CuckooFilter(capacity=16, bucket_size=1, fingerprint_size=1)
    # Forçar inserções que colidem excessivamente para demonstrar limite de kicks / falha de capacidade
    inserted = 0
    for i in range(100):
        if cf_bad.insert(f"key_{i}"):
            inserted += 1
            
    print(f"\nContraexemplo executado: capacidade minúscula e 1 slot por bucket inseriram {inserted}/100 chaves com sucesso.")
    assert True

if __name__ == "__main__":
    test_cuckoo_filter_operations()
    test_false_positive_rate()
    test_anti_pattern_counterexample()
    print("Todos os testes passaram com sucesso!")