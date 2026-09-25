// Criação de objeto EventSource
const source = new EventSource("http://localhost:8080/sse");

// Adição de listeners para eventos
source.addEventListener("evento", (event) => {
    console.log("Evento recebido:", event.data);
});

// Adição de listener para erro
source.onerror = () => {
    console.log("Erro ao receber evento");
};

// Adição de listener para fechamento da conexão
source.onclose = () => {
    console.log("Conexão fechada");
};