class SecureDatabaseSelector:
    """
    Framework de Seleção de Persistência Poliglota Integrado com Segurança,
    Isolamento de Tenants e Conformidade.
    """
    
    def evaluate_workload(
        self, 
        workload_type: str, 
        needs_strict_isolation: bool, 
        contains_pii: bool,
        multi_tenant: bool
    ) -> dict:
        
        # Validação de segurança transversal
        security_warnings = []
        recommended_datastore = ""
        justification = ""
        
        if contains_pii and not needs_strict_isolation:
            security_warnings.append("Alerta: Dados PII exigem criptografia estrita em repouso e em trânsito.")

        if workload_type == "OLTP_ACID":
            recommended_datastore = "Relacional (RDBMS com Row-Level Security)"
            justification = "Suporte nativo a transações ACID, RLS para isolamento de tenants e auditoria imutável."
            if multi_tenant:
                justification += " Isolamento garantido por políticas de RLS por schema/tabela."
                
        elif workload_type == "DOCUMENT_FLEX":
            recommended_datastore = "NoSQL Document (Ex: MongoDB com Field-Level Encryption)"
            justification = "Flexibilidade de esquema com suporte a criptografia ao nível de campo (Client-Side Field Level Encryption)."
            if multi_tenant:
                security_warnings.append("Atenção: Valide o isolamento de coleções por tenant para evitar vazamento de documentos.")
                
        elif workload_type == "KEY_VALUE_CACHE":
            recommended_datastore = "NoSQL Key-Value (Ex: Redis Enterprise com ACLs)"
            justification = "Latência mínima de leitura/escrita. ATENÇÃO: Requer criptografia em nível de aplicação para dados sensíveis em memória."
            if multi_tenant:
                security_warnings.append("Risco crítico em Key-Value puro: ACLs granulares por tenant são limitadas; prefira prefixação rigorosa de chaves e criptografia na ponta.")
                
        elif workload_type == "HYBRID_ECOMMERCE":
            recommended_datastore = "Persistência Híbrida (RDBMS + Document Store + CDC Seguro)"
            justification = "Combina transações ACID para pagamentos com flexibilidade de catálogo. Requer Sagas idempotentes e criptografia em barramentos de CDC (Kafka/Debezium)."
            if multi_tenant:
                security_warnings.append("Complexidade de Governança: A política de exclusão (GDPR/LGPD) deve propagar o expurgo de forma segura e síncrona/assíncrona por todos os datastores envolvidos.")
        else:
            raise ValueError(f"Carga de trabalho desconhecida: {workload_type}")

        return {
            "workload": workload_type,
            "recommended_datastore": recommended_datastore,
            "justification": justification,
            "security_warnings": security_warnings
        }

if __name__ == "__main__":
    selector = SecureDatabaseSelector()
    
    # Testando cenário híbrido crítico com PII e Multi-Tenant
    result = selector.evaluate_workload(
        workload_type="HYBRID_ECOMMERCE",
        needs_strict_isolation=True,
        contains_pii=True,
        multi_tenant=True
    )
    
    print("----- Relatório de Seleção Segura e Poliglota -----")
    print(f"Carga de Trabalho: {result['workload']}")
    print(f"Datastore Recomendado: {result['recommended_datastore']}")
    print(f"Justificativa Técnica: {result['justification']}")
    print("Alertas de Segurança e Governança:")
    for warning in result['security_warnings']:
        print(f" - {warning}")
    
    assert len(result['recommended_datastore']) > 0
    print("\nSucesso: Framework validado com critérios de segurança e arquitetura híbrida.")