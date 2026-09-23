import unittest
from extractor import CacheDocExtractor

class TestCacheDocExtractor(unittest.TestCase):

    def test_extract_patterns_and_ttls(self):
        source = """
        import redis
        r = redis.Redis()
        r.setex("user:100:profile", 3600, "data")
        r.expire("session:token:abc", 1800)
        r.delete("user:100:profile")
        pattern = "product:{id}:details"
        """
        extractor = CacheDocExtractor()
        extractor.parse_source_code(source)
    
        md = extractor.generate_markdown()
    
        self.assertIn("user:100:profile", extractor.cache_patterns)
        self.assertIn("product:{id}:details", extractor.cache_patterns)
        self.assertIn("session:token:abc", extractor.ttls)
        self.assertEqual(extractor.ttls["session:token:abc"], 1800)
        self.assertIn("# Relatório Automatizado", md)

    def test_extract_redis_conf(self):
        config = """
        # Configuração padrão do Redis
        maxmemory 2gb
        maxmemory-policy allkeys-lru
        """
        extractor = CacheDocExtractor()
        extractor.parse_config(config)
        
        self.assertEqual(extractor.invalidation_rules[0]["target"], "allkeys-lru")

    def test_empty_source_graceful_handling(self):
        source = "print('Hello World without cache')"
        extractor = CacheDocExtractor()
        extractor.parse_source_code(source)
        md = extractor.generate_markdown()
        
        self.assertIn("_Nenhum padrão estático de chave detectado._", md)

if __name__ == '__main__':
    unittest.main()