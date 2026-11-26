import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.propagators.w3c import W3CTraceContextPropagator
from opentelemetry.context import attach, detach, set_current_context
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.semconv.resource import ResourceAttributes

# 1. Configuração básica do Tracer (simulando um ambiente onde o backend está configurado)
provider = TracerProvider(resource=Resource.create(
    {ResourceAttributes.SERVICE_NAME: "distributed-app"}
))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

def service_b_handler(context_headers: dict) -> str:
    """Simula o Service B recebendo a chamada e extraindo o contexto."""
    # Extrai o contexto dos cabeçalhos recebidos
    context = CompositePropagator([W3CTraceContextPropagator()]).extract(context_headers)
    
    # Define o contexto extraído como o contexto atual para o Service B
    token = attach(context)
    try:
        # Cria um span no Service B, que deve herdar o trace_id do Service A
        with tracer.start_as_current_span("service_b_operation") as span_b:
            # Verifica se o contexto foi extraído corretamente
            span_b_context = span_b.get_span_context()
            trace_id_b = span_b_context.trace_id
            
            print(f"Service B Trace ID: {trace_id_b}")
            return str(trace_id_b)
    finally:
        detach(token)

def service_a_caller():
    """Simula o Service A iniciando a chamada e injetando o contexto."""
    # Inicia o span no Service A
    with tracer.start_as_current_span("service_a_operation") as span_a:
        span_a_context = span_a.get_span_context()
        trace_id_a = span_a_context.trace_id
        print(f"Service A Trace ID: {trace_id_a}")
        
        # 3. Injeção de Contexto (Propagação)
        carrier = {}
        # Injeta o contexto atual (do span_a) nos cabeçalhos
        CompositePropagator([W3CTraceContextPropagator()]).inject(carrier, context=set_current_context(span_a_context))
        
        print("\n--- Contexto Injetado (Headers) ---")
        print(carrier)
        print("-----------------------------------\n")
        
        # 4. Chamada simulada para Service B
        trace_id_b = service_b_handler(carrier)
        
        # 5. Verificação de Correlação
        if trace_id_a == trace_id_b:
            print("\n✅ SUCESSO: Trace IDs correlacionados com sucesso entre Service A e Service B.")
        else:
            print("\n❌ FALHA: Trace IDs não correlacionados.")

if __name__ == "__main__":
    service_a_caller()