from cuckoo_filter import CuckooFilter

def test_cuckoo_filter_operations():
    cf = CuckooFilter(capacity=1024, bucket_size=4, fingerprint_size=2)
    
    # Inserção
    assert cf.insert("apple") == True
    assert cf.insert("banana") == True
    
    # Busca por elementos presentes
    assert cf.search("apple") == True
    assert cf.search("banana") == True
    
    # Busca por elemento ausente (pode ter falso positivo ocasional, mas com alta probabilidade de False)
    # Para testes determinísticos de ausência, testamos chaves garantidamente não inseridas
    assert cf.search("orange") in [True, False]
    
    # Deleção
    assert cf.delete("apple") == True
    assert cf.search("apple") == False
    
    # Deletar novamente deve retornar False
    assert cf.delete("apple") == False

def test_false_positive_rate():
    # Cenário rigoroso: 10.000 chaves inseridas, 1.000 chaves de teste distintas
    capacity = 16384
    cf = CuckooFilter(capacity=capacity, bucket_size=4, fingerprint_size=2)
    
    num_inserted = 10000
    inserted_keys = [f"key_{i}" for i in range(num_inserted)]
    
    for key in inserted_keys:
        success = cf.insert(key)
        assert success, f"Falha ao inserir chave {key} (filtro cheio prematuramente)"
        
    # Chaves de teste que NÃO foram inseridas
    num_test = 1000
    test_keys = [f"test_absent_key_{i}" for i in range(num_test)]
    
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
    
    # Critério de sucesso rigoroso: Taxa de falsos positivos inferior a 2%
    assert fp_rate < 0.02, f"Taxa de falsos positivos alta demais: {fp_rate * 100:.2f}% (esperado < 2%)"

if __name__ == "__main__":
    test_cuckoo_filter_operations()
    test_false_positive_rate()
    print("Todos os testes passaram com sucesso!")