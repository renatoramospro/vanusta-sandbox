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
    if not filters:
        return ["Nenhum filtro aplicado."]
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
                descriptions.append(f"Aplica o filtro do tipo `{ftype}`.")
        else:
            descriptions.append("Filtro personalizado complexo.")
    return descriptions

def parse_actions(actions):
    """Converte ações técnicas em descrição de remediação legível por não técnicos."""
    descriptions = []
    if not actions:
        return ["Nenhuma ação automática configurada (apenas auditoria)."]
    for a in actions:
        if isinstance(a, str):
            descriptions.append(f"Ação: `{a}`")
        elif isinstance(a, dict):
            atype = a.get('type', 'desconhecido')
            if atype == 'mark-for-op':
                descriptions.append(f"Marca o recurso afetado para a operação de `{a.get('op')}`.")
            elif atype == 'stop':
                descriptions.append("Interrompe (desliga) o recurso afetado imediatamente.")
            elif atype == 'notify':
                descriptions.append("Envia uma notificação aos responsáveis.")
            else:
                descriptions.append(f"Executa a ação do tipo `{atype}`.")
        else:
            descriptions.append("Ação personalizada.")
    return descriptions

def convert_c7n_to_markdown(yaml_content):
    """Converte o conteúdo YAML do Cloud Custodian em um catálogo Markdown estruturado."""
    data = yaml.safe_load(yaml_content)
    policies = data.get('policies', [])
    
    markdown_lines = ["# Catálogo de Políticas de Segurança em Nuvem (Cloud Custodian)\n"]
    markdown_lines.append("Este documento é gerado automaticamente a partir das definições de políticas ativas.\n")
    
    active_policies_count = 0
    
    for p in policies:
        name = p.get('name', 'sem-nome')
        # Correção: Considera rascunho apenas se o nome contiver 'draft' ou houver flag explícita
        if 'draft' in name.lower():
            continue
            
        active_policies_count += 1
        resource = p.get('resource', 'desconhecido')
        comment = p.get('comment', 'Sem descrição fornecida.').strip()
        
        markdown_lines.append(f"## Política: `{name}`\n")
        markdown_lines.append(f"- **Objetivo:** {comment}")
        markdown_lines.append(f"- **Recurso Afetado:** ` {resource} `")
        
        markdown_lines.append("- **Filtros Aplicados:**")
        for f_desc in parse_filters(p.get('filters', [])):
            markdown_lines.append(f"  - {f_desc}")
            
        markdown_lines.append("- **Ações e Remediação:**")
        for a_desc in parse_actions(p.get('actions', [])):
            markdown_lines.append(f"  - {a_desc}")
            
        markdown_lines.append("\n---\n")
        
    return "\n".join(markdown_lines), active_policies_count