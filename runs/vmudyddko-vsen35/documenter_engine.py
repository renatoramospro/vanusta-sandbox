import yaml
import sys
import os

# Pipeline YAML simulado para teste robusto e reprodutível
SAMPLE_PIPELINE_YAML = """
name: Enterprise CI/CD Pipeline
variables:
  GLOBAL_TIMEOUT: "30"
  REGISTRY: "registry.internal.net"

stages:
  - validate
  - build
  - deploy

jobs:
  lint_code:
    stage: validate
    image: python:3.11-slim
    script:
      - flake8 .
      - black --check .
    variables:
      LINT_STRICT: "true"

  run_unit_tests:
    stage: validate
    needs: []
    script:
      - pytest --cov=app

  build_artifact:
    stage: build
    needs: ["run_unit_tests", "lint_code"]
    script:
      - docker build -t $REGISTRY/app:latest .
      - docker push $REGISTRY/app:latest
    rules:
      - if: '$CI_COMMIT_BRANCH == "main"'
        when: on_success
      - if: '$CI_COMMIT_BRANCH == "staging"'
        when: manual

  deploy_production:
    stage: deploy
    needs: ["build_artifact"]
    script:
      - ./deploy.sh production
    environment:
      name: production
      url: https://app.internal.net
    rules:
      - if: '$CI_COMMIT_TAG =~ /^v.*/'
        when: manual
"""

def parse_pipeline(yaml_content):
    data = yaml.safe_load(yaml_content)
    return data

def generate_markdown_documentation(pipeline_data):
    md = []
    
    # Cabeçalho e Metadados
    md.append(f"# Documentação Técnica do Pipeline: {pipeline_data.get('name', 'CI/CD Pipeline')}\n")
    md.append("## 1. Visão Geral e Escopo")
    md.append("Este documento descreve automaticamente a arquitetura de entrega contínua, mapeando estágios, dependências condicionais e variáveis de ambiente.\n")
    
    # Variáveis Globais
    variables = pipeline_data.get('variables', {})
    md.append("## 2. Variáveis de Ambiente Globais")
    if variables:
        md.append("| Variável | Valor Padrão / Escopo |")
        md.append("| :--- | :--- |")
        for k, v in variables.items():
            md.append(f"| `{k}` | `{v}` |")
    else:
        md.append("*Nenhuma variável global declarada.*")
    md.append("")
    
    # Estágios e Jobs
    stages = pipeline_data.get('stages', [])
    jobs = pipeline_data.get('jobs', {})
    
    md.append("## 3. Estágios e Fluxo de Execução")
    for stage in stages:
        md.append(f"### Estágio: `{stage}`")
        stage_jobs = {jname: jdetails for jname, jdetails in jobs.items() if jdetails.get('stage') == stage}
        
        if not stage_jobs:
            md.append("*Nenhum job associado a este estágio.*\n")
            continue
            
        for jname, jdetails in stage_jobs.items():
            md.append(f"- **Job:** `{jname}`")
            
            # Dependências (Needs)
            needs = jdetails.get('needs', [])
            if needs is not None:
                if needs:
                    needs_str = ", ".join([f"`{n}`" for n in needs])
                    md.append(f"  - **Depende de (Needs):** {needs_str}")
                else:
                    md.append(f"  - **Depende de (Needs):** Execução independente (Início do pipeline)")
            
            # Regras Condicionais
            rules = jdetails.get('rules', [])
            if rules:
                md.append("  - **Regras de Execução Condicional:**")
                for r in rules:
                    cond = r.get('if', 'Condição não especificada')
                    behavior = r.get('when', 'on_success')
                    md.append(f"    - Se ` {cond} ` $\rightarrow$ Comportamento: `{behavior}`")
            
            # Variáveis locais
            j_vars = jdetails.get('variables', {})
            if j_vars:
                md.append("  - **Variáveis Locais:**")
                for vk, vv in j_vars.items():
                    md.append(f"    - `{vk}` = `{vv}`")
                    
            # Ambiente de Deploy
            env = jdetails.get('environment')
            if env:
                md.append(f"  - **Ambiente Alvo:** `{env.get('name')}` (URL: {env.get('url', 'N/A')})")
                
            md.append("")
            
    return "\n".join(md)

if __name__ == "__main__":
    print("Iniciando motor de extração e documentação de CI/CD...")
    
    # Executa o parsing
    try:
        pipeline_data = parse_pipeline(SAMPLE_PIPELINE_YAML)
        doc_markdown = generate_markdown_documentation(pipeline_data)
        
        # Salva o arquivo de saída gerado
        output_filename = "pipeline_documentation.md"
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(doc_markdown)
            
        print(f"[SUCESSO] Documentação gerada e salva em '{output_filename}'.")
        print("\n--- Amostra do Conteúdo Gerado ---")
        print(doc_markdown[:600] + "\n[...conteúdo truncado para exibição...]")
        
        # Validação de Asserção do Critério de Sucesso
        assert "# Documentação Técnica do Pipeline" in doc_markdown
        assert "lint_code" in doc_markdown
        assert "build_artifact" in doc_markdown
        assert "deploy_production" in doc_markdown
        print("\n[VERIFICAÇÃO] Todas as asserções de rastreabilidade passaram com 100% de precisão!")
        
    except Exception as e:
        print(f"[ERRO] Falha durante o processamento do pipeline: {e}")
        sys.exit(1)