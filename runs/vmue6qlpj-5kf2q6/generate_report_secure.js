const fs = require('fs');

/**
 * Função de sanitização para evitar Markdown e HTML Injection.
 * Remove ou escapa caracteres especiais e tags perigosas em strings dinâmicas.
 */
function sanitizeMarkdown(input) {
    if (typeof input !== 'string') {
        return String(input);
    }
    return input
        // Remove tags HTML para prevenir HTML Injection / XSS
        .replace(/<\/?[^>]+(>|$)/g, "")
        // Escapa caracteres especiais do Markdown que poderiam quebrar a formatação ou injetar links/imagens
        .replace(/([\\`*_{}\[\]()#+\-.!|])/g, '\\$1');
}

/**
 * Simula o objeto `data` que o k6 entrega para a função `handleSummary(data)`,
 * incluindo campos de texto que poderiam conter payloads maliciosos.
 */
function mockK6SummaryDataWithPayload() {
    return {
        metrics: {
            http_reqs: { values: { count: 12500, rate: 250.5 } },
            http_req_duration: { 
                values: { 
                    avg: 210.4, 
                    p90: 380.0, 
                    p95: 450.2, 
                    p99: 820.5  
                } 
            },
            http_req_failed: { values: { rate: 0.008 } }
        },
        state: {
            testRunDurationMs: 50000
        },
        // Simulação de metadados externos ou mensagens de erro injetadas pelo sistema testado
        metadata: {
            endpointName: "/api/v1/checkout<script>alert('XSS')</script>",
            lastErrorMsg: "Connection timeout *critical failure*"
        }
    };
}

/**
 * Função equivalente ao handleSummary(data) exigida pelo k6, agora segura contra injeções.
 */
function handleSummary(data) {
    const metrics = data.metrics;
    
    // Sanitização de entradas que vêm de fontes externas/métricas de texto
    const safeEndpoint = sanitizeMarkdown(data.metadata?.endpointName || "N/A");
    const safeErrorMsg = sanitizeMarkdown(data.metadata?.lastErrorMsg || "Nenhum");

    const totalRequests = metrics.http_reqs.values.count;
    const throughputRps = metrics.http_reqs.values.rate.toFixed(2);
    const p95 = metrics.http_req_duration.values.p95;
    const p99 = metrics.http_req_duration.values.p99;
    const errorRate = (metrics.http_req_failed.values.rate * 100).toFixed(2);

    const slaP95 = 500; 
    const slaErrorRate = 1.0; 

    const p95Passed = p95 <= slaP95;
    const errorPassed = parseFloat(errorRate) <= slaErrorRate;
    const globalStatus = (p95Passed && errorPassed) ? "✅ APROVADO" : "❌ REPROVADO";

    const markdownReport = `# Relatório Automatizado de Performance - k6 (Secure)

> **Data da Execução:** ${new Date().toISOString()}  
> **Endpoint Alvo:** \`${safeEndpoint}\`  
> **Status Geral do SLA:** ${globalStatus}

## 📊 Resumo Executivo
Este relatório foi gerado automaticamente e sanitizado contra injeções de conteúdo.

| Métrica Analisada | Valor Medido | Limite de SLA Esperado | Status |
| :--- | :--- | :--- | :--- |
| **Throughput (RPS)** | \`${throughputRps} req/s\` | N/A (Informativo) | ℹ️ |
| **Latência p95** | \`${p95} ms\` | \`< 500 ms\` | ${p95Passed ? '✅ OK' : '❌ Falha'} |
| **Latência p99** | \`${p99} ms\` | \`< 800 ms\` | ⚠️ Alerta na Cauda |
| **Taxa de Erros** | \`${errorRate}%\` | \`< 1%\` | ${errorPassed ? '✅ OK' : '❌ Falha'} |

## 🔍 Análise Detalhada e Justificativa
- **Volume:** Foram processadas \`${totalRequests}\` requisições totais.
- **Última Mensagem Registrada:** \`${safeErrorMsg}\`
- **Latência de Cauda:** O p99 atingiu \`${p99}ms\`, indicando gargalos esporádicos sob alta concorrência.
`;

    return {
        'performance-report.md': markdownReport
    };
}

// Execução e validação do experimento seguro
const summaryData = mockK6SummaryDataWithPayload();
const files = handleSummary(summaryData);
const reportContent = files['performance-report.md'];

fs.writeFileSync('performance-report.md', reportContent);

console.log("=== RELATÓRIO SEGURO GERADO COM SUCESSO ===");
console.log(reportContent);

// Validação de que a tag <script> foi neutralizada com sucesso
if (reportContent.includes("<script>") || reportContent.includes("alert('XSS')")) {
    console.error("Erro de Segurança: O payload malicioso não foi sanitizado!");
    process.exit(1);
}

console.log("Validação de segurança concluída com sucesso: código de saída 0.");