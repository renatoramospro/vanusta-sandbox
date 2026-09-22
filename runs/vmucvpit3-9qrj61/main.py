import random

def calcular_probabilidade_estouro_capacidade(rps, latency, conexoes):
    return (rps / (rps + 1)) * (latency / (latency + 1)) * (conexoes / (conexoes + 1))

def simular_carga(rps, latency, conexoes, num_simulacoes):
    resultados = []
    for _ in range(num_simulacoes):
        probabilidade_estouro_capacidade = calcular_probabilidade_estouro_capacidade(rps, latency, conexoes)
        resultados.append(probabilidade_estouro_capacidade)
    return resultados

def main():
    rps = 10000
    latency = 200
    conexoes = 500
    num_simulacoes = 1000

    resultados = simular_carga(rps, latency, conexoes, num_simulacoes)

    media = sum(resultados) / len(resultados)
    print(f"Media: {media}")

    erro_preditivo = abs(media - 0.05)
    print(f"Erro Preditivo: {erro_preditivo}")

if __name__ == "__main__":
    main()