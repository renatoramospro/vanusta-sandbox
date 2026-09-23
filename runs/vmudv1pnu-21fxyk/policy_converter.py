import os
import yaml

# Exemplo de arquivo de políticas do Cloud Custodian simulando o repositório
SAMPLE_POLICIES_YAML = """
policies:
  - name: s3-bucket-public-read-prohibited
    resource: aws.s3
    comment: |
      Garante que nenhum bucket S3 tenha permissão de leitura pública (ACL ou Policy).
    mode:
      type: periodic
      schedule: rate(1 hour)
    filters:
      - type: bucket-acl
        operator: eq
        value: PUBLIC
    actions:
      - type: mark-for-op
        op: delete

  - name: ec2-require-imdsv2
    resource: aws.ec2
    comment: |
      Exige o uso exclusivo do IMDSv2 em instâncias EC2 para prevenir SSRF.
    filters:
      - type: value
        key: MetadataOptions.HttpTokens
        value: optional
    actions:
      - type: stop

  - name: draft-test-policy
    resource: aws.rds
    mode: null
    comment: Política em rascunho, não deve entrar no catálogo oficial.
    filters:
      - type: value
        key: Engine
        value: mysql
    actions:
      - type: notify
"""

def parse_filters(filters):
    """Converte filtros técnicos em descrição em linguagem natural amigável."""
    descriptions = []
    for f in filters:
        if isinstance(f, str):
            descriptions.append(f"Filtro baseado na string: `{f}`")
        elif isinstance(f, dict):
            ftype = f.get('type', 'desconhecido')
            if ftype == 'bucket-acl':
                descriptions.append(f"Verifica se a ACL do bucket S3 possui o valor `{f.get('value')}`.")
            elif ftype == 'value':
                descriptions.append(f"Filtra instâncias onde a chave `{f.get('key')}` é igual a `{f.get('value')}`.")
            else:
                descriptions.append(f"Aplica o filtro do tipo `{ftype}` com os parâmetros: `{f}`")
    return descriptions

def parse_actions(actions):
    """Converte ações técnicas em descrições legíveis para não técnicos."""
    descriptions = []
    for a in actions:
        if isinstance(a, str):
            descriptions.append(f"Ação: `{a}`")
        elif isinstance(a, dict):
            atype = a.get('type', 'desconhecido')
            if atype == 'mark-for-op':
                descriptions.append(f"Marca o recurso para operação futura de `{a.get('op')}`.")
            elif atype == 'stop':
                descriptions.append("Interrompe a execução do recurso afetado.")
            elif atype == 'notify':
                descriptions.append("Envia uma notificação aos responsáveis.")
            else:
                descriptions.append(f"Executa a ação do tipo `{atype}`.")
    return descriptions

def convert_c7n_to_markdown(yaml_content):
    """
    Converte o conteúdo YAML do Cloud Custodian em um catálogo Markdown estruturado,
    filtrando políticas em rascunho ou desativadas (mode: null).
    Retorna o texto gerado e a contagem de políticas ativas processadas.
    """
    data = yaml.safe_load(yaml_content)
    policies = data.get('policies', [])
    
    md_lines = ["# Catálogo de Conformidade e Políticas de Segurança", ""]
    md_lines.append("Este documento é gerado automaticamente a partir das definições de infraestrutura como código (Cloud Custodian).\n")
    
    active_count = 0
    for policy in policies:
        # Critério de conformidade: ignora políticas sem modo ou marcadas como rascunho
        if policy.get('mode') is None:
            continue
            
        active_count += 1
        name = policy.get('name', 'Sem Nome')
        resource = policy.get('resource', 'Recurso desconhecido')
        comment = policy.get('comment', 'Sem descrição fornecida.').strip()
        
        md_lines.append(f"## Política: `{name}`")
        md_lines.append(f"- **Objetivo:** {comment}")
        md_lines.append(f"- **Recurso Afetado:** `{resource}`")
        
        md_lines.append("- **Filtros Aplicados:**")
        filters = policy.get('filters', [])
        for f_desc in parse_filters(filters):
            md_lines.append(f"  - {f_desc}")
            
        md_lines.append("- **Ações e Remediação:**")
        actions = policy.get('actions', [])
        for a_desc in parse_actions(actions):
            md_lines.append(f"  - {a_desc}")
            
        md_lines.append("\n---\n")
        
    return "\n".join(md_lines), active_count