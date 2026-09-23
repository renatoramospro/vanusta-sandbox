import unittest
from extractor import CacheDocExtractor

class TestCacheDocExtractor(unittest.TestCase):

    def test_advanced_scenarios(self):
        source = """
        # Comentário que deve ser ignorado
        CACHE_TTL = 15 * 60
        EXPR_TTL = 3600
        
        def process_cache(r):
            # Chave interpolada
            user_key = f"user:{id}:profile"
            r.setex(user_key, CACHE_TTL, "data")
            
            # TTL por constante e argumento ex=
            r.set("product:123:details", "details", ex=EXPR_TTL)
            
            # Chave sem dois pontos e invalidação
            r.expire("sessiontokenabc", 1800)
            r.delete("user:100:profile")
            
            # Falso positivo simulado (URL/Mensagem)
            url = "http://example.com/api/v1"
            msg = "Error: cache failed"
        """
        extractor = CacheDocExtractor()
        extractor.parse_source_code(source)
        
        md = extractor.generate_markdown()

        # Verificações de robustez
        self.assertIn("user:{id}:profile", extractor.cache_patterns)
        self.assertIn("product:123:details", extractor.cache_patterns)
        self.assertIn("sessiontokenabc", extractor.cache_patterns)
        
        # Verifica resolução de expressões aritméticas (15 * 60 = 900)
        self.assertEqual(extractor.ttls.get("user:{id}:profile"), 900)
        self.assertEqual(extractor.ttls.get("product:123:details"), 3600)
        self.assertEqual(extractor.ttls.get("sessiontokenabc"), 1800)
        
        # Garante exclusão de falsos positivos (URLs)
        self.assertNotIn("http://example.com/api/v1", extractor.cache_patterns)
        
        # Valida relatório Markdown gerado
        self.assertIn("# Relatório Automatizado", md)
        self.assertIn("user:{id}:profile", md)

    def test_redis_conf_parsing(self):
        config = """
        # Arquivo de configuração
        maxmemory-policy volatile-lru
        save 900 1
        """
        extractor = CacheDocExtractor()
        extractor.parse_config(config)
        self.assertEqual(len(extractor.invalidation_rules), 2)
        self.assertEqual(extractor.invalidation_rules[0]["target"], "volatile-lru")

    def test_empty_source(self):
        extractor = CacheDocExtractor()
        extractor.parse_source_code("")
        md = extractor.generate_markdown()
        self.assertIn("_Nenhum padrão estático de chave detectado._", md)

if __name__ == '__main__':
    unittest.main()