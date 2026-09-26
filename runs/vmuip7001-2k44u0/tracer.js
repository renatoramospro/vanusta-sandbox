const { AsyncLocalStorage } = require('async_hooks');
const assert = require('assert');
const crypto = require('crypto');

// Armazenamento de contexto assíncrono (AsyncLocalStorage)
const asyncLocalStorage = new AsyncLocalStorage();

class Tracer {
    constructor() {
        this.logs = [];
    }

    // Gera ID único hexadecimal
    _generateId(bytes = 8) {
        return crypto.randomBytes(bytes).toString('hex');
    }

    // Registra log estruturado e guarda em memória para validação
    _log(level, message, extra = {}) {
        const store = asyncLocalStorage.getStore() || {};
        const logEntry = {
            timestamp: new Date().toISOString(),
            level,
            message,
            traceId: store.traceId || null,
            spanId: store.spanId || null,
            parentId: store.parentId || null,
            ...extra
        };
        this.logs.push(logEntry);
        console.log(JSON.stringify(logEntry));
    }

    // Inicia um novo Trace (Raiz)
    async startTrace(name, fn) {
        const traceId = this._generateId(8);
        const spanId = this._generateId(4);

        const context = { traceId, spanId, parentId: null };

        return asyncLocalStorage.run(context, async () => {
            this._log('INFO', `Início do Trace: ${name}`, { operation: name });
            try {
                return await fn();
            } finally {
                this._log('INFO', `Fim do Trace: ${name}`, { operation: name });
            }
        });
    }

    // Inicia um Span Filho propagando o contexto anterior corretamente
    async startSpan(name, fn) {
        const parentStore = asyncLocalStorage.getStore();
        if (!parentStore) {
            throw new Error("Tentativa de iniciar span sem um contexto ativo (Trace raiz ausente)");
        }

        const traceId = parentStore.traceId;
        const parentId = parentStore.spanId;
        const spanId = this._generateId(4);

        const childContext = { traceId, spanId, parentId };

        return asyncLocalStorage.run(childContext, async () => {
            this._log('INFO', `Início do Span: ${name}`, { operation: name });
            try {
                return await fn();
            } finally {
                this._log('INFO', `Fim do Span: ${name}`, { operation: name });
            }
        });
    }
}

// Simulação da árvore de chamadas de 3 níveis
async function runSimulation() {
    const tracer = new Tracer();

    console.log("--- INICIANDO SIMULAÇÃO DE TRACING DISTRIBUÍDO ---");

    await tracer.startTrace("Nivel1-Raiz", async () => {
        // Simulando trabalho assíncrono no nível 1
        await new Promise(resolve => setTimeout(resolve, 10));

        await tracer.startSpan("Nivel2-Filho", async () => {
            // Simulando trabalho assíncrono no nível 2
            await new Promise(resolve => setTimeout(resolve, 10));

            await tracer.startSpan("Nivel3-Neto", async () => {
                console.log("Executando operação no fundo da árvore (Nível 3)");
                await new Promise(resolve => setTimeout(resolve, 10));
            });
        });
    });

    console.log("\n--- INICIANDO VALIDAÇÃO AUTOMATIZADA DOS LOGS ---");
    
    const logs = tracer.logs;
    assert.strictEqual(logs.length, 6, "Deveria haver exatamente 6 entradas de log (3 inícios e 3 fins)");

    const traceIdRaiz = logs[0].traceId;
    assert.ok(traceIdRaiz, "Log raiz deve conter traceId");

    const spanIdsVistos = new Set();
    const activeSpans = new Map();

    for (const log of logs) {
        // 1. Todos os logs compartilham o mesmo traceId
        assert.strictEqual(log.traceId, traceIdRaiz, "Todos os logs devem pertencer ao mesmo traceId");
        
        // 2. Cada log deve conter spanId
        assert.ok(log.spanId, "Log deve conter spanId");

        if (log.message.startsWith("Início do")) {
            assert.strictEqual(activeSpans.has(log.spanId), false, `SpanId duplicado encontrado no início: ${log.spanId}`);
            activeSpans.set(log.spanId, log);
            spanIdsVistos.add(log.spanId);
        } else if (log.message.startsWith("Fim do")) {
            // O spanId no fim deve corresponder exatamente ao spanId que iniciou
            assert.ok(activeSpans.has(log.spanId), `SpanId de término não encontrado nos ativos: ${log.spanId}`);
            activeSpans.delete(log.spanId);
        }
    }

    // 3. Validação de hierarquia de parentId
    // Log 0: Nível 1 Início (parentId: null)
    assert.strictEqual(logs[0].parentId, null, "Raiz não deve ter parentId");
    
    // Log 1: Nível 2 Início (parentId deve ser o spanId do Nível 1 Início)
    assert.strictEqual(logs[1].parentId, logs[0].spanId, "Nível 2 deve ter como parentId o spanId do Nível 1");

    // Log 2: Nível 3 Início (parentId deve ser o spanId do Nível 2 Início)
    assert.strictEqual(logs[2].parentId, logs[1].spanId, "Nível 3 deve ter como parentId o spanId do Nível 2");

    console.log(`Validação concluída com sucesso! Total de logs analisados: ${logs.length}`);
    console.log("100% das operações correlacionadas com traceId e spanId consistentes.");
}

runSimulation().catch(err => {
    console.error("Falha no experimento:", err);
    process.exit(1);
});