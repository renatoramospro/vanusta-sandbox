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
    """Converte ações técnicas em remediações legíveis para não-técnicos."""
    descriptions = []
    for a in actions:
        if isinstance(a, str):
            descriptions.append(f"Ação executada: `{a}`")
        elif isinstance(a, dict):
            atype = a.get('type', 'desconhecido')
            if atype == 'mark-for-op':
                descriptions.append(f"Marca o recurso para execução posterior da operação: `{a.get('op')}`.")
            elif atype == 'stop':
                descriptions.append("Interrompe (para) o recurso imediatamente.")
            elif atype == 'notify':
                descriptions.append("Envia uma notificação aos responsáveis.")
            else:
                descriptions.append(f"Executa a ação `{atype}`.")
    return descriptions

def convert_c7n_to_markdown(yaml_content):
    """Converte YAML do Cloud Custodian em catálogo Markdown formatado para conformidade."""
    data = yaml.safe_load(yaml_content)
    policies = data.get('policies', [])
    
    md_lines = ["# Catálogo de Políticas de Segurança em Nuvem (Cloud Custodian)\n"]
    md_lines.append("Este documento é gerado automaticamente a partir do repositório de infraestrutura.\n")
    md_lines.append("---")
    
    active_count = 0
    for p in policies:
        # Equívoco comum evitado aqui: ignorar políticas em rascunho/desativadas (mode: null)
        if p.get('mode') is None and 'draft' in p.get('name', ''):
            continue
            
        active_count += 1
        name = p.get('name')
        resource = p.get('resource')
        comment = p.get('comment', 'Sem descrição fornecida.').strip()
        filters = p.get('filters', [])
        actions = p.get('actions', [])
        
        md_lines.append(f"\n## Política: `{name}`\n")
        md_lines.append(f"**Objetivo:** {comment}\n")
        md_lines.append(f"**Recurso Afetado:** `{resource}`\n")
        
        md_lines.append("**Filtros Aplicados:**")
        for f_desc in parse_filters(filters):
            md_lines.append(f"- {f_desc}")
            
        md_lines.append("\n**Ações e Remediação:**")
        for a_desc in parse_actions(actions):
            md_lines.append(f"- {a_desc}")
            
        md_lines.append("\n---\n")
        
    return "\n".join(md_lines), active_count

if __name__ == "__main__":
    markdown_output, count = convert_c7n_to_markdown(SAMPLE_POLICIES_YAML)
    print(f"Total de políticas ativas convertidas: {count}")
    print("\n--- Prévia do Markdown Gerado ---\n")
    print(markdown_output[:500] + "\n...\n[Truncado para visualização]")