import pytest
from policy_converter import convert_c7n_to_markdown, SAMPLE_POLICIES_YAML

def test_conversion_active_policies_only():
    """Garante que políticas desativadas/rascunhos são ignoradas e apenas ativas entram no catálogo."""
    markdown, count = convert_c7n_to_markdown(SAMPLE_POLICIES_YAML)
    
    # O YAML de exemplo tem 3 políticas, sendo 1 rascunho ('draft-test-policy')
    assert count == 2, f"Esperado 2 políticas ativas, mas foram encontradas {count}"
    assert "draft-test-policy" not in markdown, "Erro: Política em rascunho vazou para o catálogo oficial de conformidade!"
    assert "s3-bucket-public-read-prohibited" in markdown
    assert "ec2-require-imdsv2" in markdown

def test_no_raw_json_yaml_exposed():
    """Garante que a documentação gerada explica os termos em vez de expor blocos de código crus."""
    markdown, _ = convert_c7n_to_markdown(SAMPLE_POLICIES_YAML)
    # Verifica se seções padronizadas foram criadas para o stakeholder não técnico
    assert "**Objetivo:**" in markdown
    assert "**Recurso Afetado:**" in markdown
    assert "**Filtros Aplicados:**" in markdown
    assert "**Ações e Remediação:**" in markdown