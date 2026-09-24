import pytest
from pydantic import ValidationError
from pulsar_doc_generator import generate_markdown_from_yaml, PulsarClusterConfig

def test_successful_markdown_generation():
    yaml_data = """
    cluster_name: "cluster-teste"
    tenant: "tenant-x"
    namespace: "ns-y"
    topics:
      - name: "topico-a"
        type: "persistent"
        partitions: 2
        subscriptions:
          - name: "sub-1"
            type: "Exclusive"
    """
    markdown = generate_markdown_from_yaml(yaml_data)
    assert "# Documentação do Cluster Apache Pulsar: cluster-teste" in markdown
    assert "topico-a" in markdown
    assert "Exclusive" in markdown
    assert "2" in markdown

def test_invalid_subscription_type_raises_error():
    invalid_yaml = """
    cluster_name: "cluster-teste"
    tenant: "tenant-x"
    namespace: "ns-y"
    topics:
      - name: "topico-a"
        type: "persistent"
        partitions: 1
        subscriptions:
          - name: "sub-invalid"
            type: "SuperDuperShared" 
    """
    with pytest.raises(ValidationError) as excinfo:
        generate_markdown_from_yaml(invalid_yaml)
    
    assert "Input should be 'Exclusive', 'Shared', 'Failover' or 'Key_Shared'" in str(excinfo.value)
    print("Sucesso: Validação de esquema rejeitou tipo de assinatura inválido conforme esperado.")