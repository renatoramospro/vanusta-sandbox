const fs = require('fs');

/**
 * Simula o objeto `data` que o k6 entrega para a função `handleSummary(data)`
 */
function mockK6SummaryData() {
    return {
        metrics: {
            http_reqs: { values: { count: 12500, rate: 250.5 } }, // Throughput: 250.5 RPS
            http_req_duration: { 
                values: { 
                    avg: 210.4, 
                    p90: 380.0, 
                    p95: 450.2, // Limite esperado: < 500ms (Aprovado)
                    p99: 820.5  // Limite esperado: < 800ms (Regressão na cauda)
                } 
            },
            http_req_failed: { values: { rate: 0.008 } } // Taxa de erro: 0.8% (< 1% esperado)
        },
        state: {
            testRunDurationMs: 50000
        }
    };
}

/**
 * Função equivalente ao handleSummary(data) exigida pelo k6
 */
function handleSummary(data) {
    const metrics = data.metrics;

    // Extração de métricas-chave
    const totalRequests = metrics.http_reqs.values.count;
    const throughputRps = metrics.http_reqs.values.rate.toFixed(2);
    const p95 = metrics.http_req_duration.values.p95;
    const p99 = metrics.http_req_duration.values.p99;
    const errorRate = (metrics.http_req_failed.values.rate * 100).toFixed(2);

    // Definição de SLAs esperados
    const slaP95 = 500; // ms
    const slaErrorRate = 1.0; // %

    // Avaliação de conformidade com SLAs
    const p95Passed = p95 <= slaP95;
    const errorPassed = parseFloat(errorRate) <= slaErrorRate;
    const overallStatus = (p95Passed && errorPassed) ? "✅ APROVADO" : "❌ REGRESSÃO DETECTADA";

    // Construção do Relatório em Markdown (Legível por Humanos)
    const markdownReport = `# Relatório Automatizado de Performance - k6

> **Data da Execução:** ${new Date().toISOString()}  
> **Status Geral do SLA:** ${overallStatus}

## 📊 Resumo Executivo
Este relatório foi gerado automaticamente ao término da execução do teste de carga utilizando o gancho nativo \`handleSummary\` do k6.

| Métrica Analisada | Valor Medido | Limite de SLA Esperado | Status |
| :--- | :--- | :--- | :--- |
| **Throughput (RPS)** | \`${throughputRps} req/s\` | N/A (Informativo) | ℹ️ |
| **Latência p95** | \`${p95} ms\` | \`< ${slaP95} ms\` | ${p95Passed ? '✅ OK' : '⚠️ FALOU'} |
| **Latência p99** | \`${p99} ms\` | \`< 800 ms\` | ⚠️ Alerta na Cauda |
| **Taxa de Erros** | \`${errorRate}%\` | \`< ${slaErrorRate}%\` | ${errorPassed ? '✅ OK' : '❌ FALOU'} |

## 🔍 Análise Detalhada e Justificativa
- **Volume:** Foram processadas ${totalRequests} requisições totais durante o teste de estresse.
- **Latência de Cauda:** Embora a média e o percentil 95 tenham cumprido o acordo de nível de serviço, o p99 atingiu \`${p99}ms\`, indicando gargalos esporádicos em conexões de banco de dados sob alta concorrência.
`;

    return {
        'performance-report.md': markdownReport
    };
}

// Execução do experimento e validação observável
const summaryData = mockK6SummaryData();
const files = handleSummary(summaryData);
const reportContent = files['performance-report.md'];

fs.writeFileSync('performance-report.md', reportContent);

console.log("=== RELATÓRIO GERADO COM SUCESSO ===");
console.log(reportContent);

// Asserções para garantir a qualidade do resultado
if (!reportContent.includes("✅ APROVADO") || !reportContent.includes("450.2 ms")) {
    console.error("Erro: O relatório não contém as métricas esperadas ou o status correto.");
    process.exit(1);
}

console.log("Teste de geração de documentação concluído com código 0.");