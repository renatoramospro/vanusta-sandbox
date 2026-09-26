import sys
from typing import List, Tuple, Dict, Any

# --- NÍVEL 1 & 2: O Algoritmo de Myers (SES) ---

def myers_diff(a: List[str], b: List[str]) -> List[Tuple[str, str]]:
    """
    Calcula o Shortest Edit Script (SES) entre duas listas de linhas usando o algoritmo de Myers.
    Retorna uma lista de tuplas (' ', linha), ('-', linha) ou ('+', linha).
    """
    N = len(a)
    M = len(b)
    max_d = N + M
    v = {1: 0}
    trace = []

    for d in range(max_d + 1):
        v_current = dict(v)
        for k in range(-d, d + 1, 2):
            if k == -d or (k != d and v.get(k - 1, -1) < v.get(k + 1, -1)):
                x = v[k + 1]
                v_direction = 'down'
            else:
                x = v[k - 1] + 1
                v_direction = 'right'

            y = x - k
            
            # Seguir diagonais (matches)
            while x < N and y < M and a[x] == b[y]:
                x += 1
                y += 1

            v[k] = x
            if x >= N and y >= M:
                trace.append(v_current)
                return _backtrace(trace, a, b)
        trace.append(v_current)
    return []

def _backtrace(trace: List[Dict[int, int]], a: List[str], b: List[str]) -> List[Tuple[str, str]]:
    x = len(a)
    y = len(b)
    script = []

    for d in range(len(trace) - 1, -1, -1):
        v = trace[d]
        k = x - y
        
        if k == -d or (k != d and v.get(k - 1, -1) < v.get(k + 1, -1)):
            prev_k = k + 1
        else:
            prev_k = k - 1

        prev_x = v.get(prev_k, 0)
        prev_y = prev_x - prev_k

        while x > prev_x and y > prev_y:
            script.append((' ', a[x - 1]))
            x -= 1
            y -= 1

        if d > 0:
            if prev_x == x:
                script.append(('+', b[prev_y]))
                y -= 1
            else:
                script.append(('-', a[prev_x]))
                x -= 1
        
    script.reverse()
    return script

# --- NÍVEL 4: Geração de Unified Diff ---

def generate_unified_diff(a: List[str], b: List[str], from_file: str = "a", to_file: str = "b") -> str:
    script = myers_diff(a, b)
    if not script:
        return ""

    lines = [f"--- {from_file}\n", f"+++ {to_file}\n"]
    
    # Simplificação de hunk único para demonstração robusta
    hunk_lines = []
    for op, line in script:
        if op == ' ':
            hunk_lines.append(f" {line}")
        elif op == '-':
            hunk_lines.append(f"-{line}")
        elif op == '+':
            hunk_lines.append(f"+{line}")

    # Cabeçalho do hunk simples
    hunk_header = f"@@ -1,{len(a)} +1,{len(b)} @@\n"
    lines.append(hunk_header)
    lines.extend(hunk_lines)
    
    return "".join(lines)

# --- NÍVEL 5: Aplicação de Patch Corrigida ---

def apply_patch(original: List[str], diff_str: str) -> List[str]:
    """
    Aplica um patch Unified Diff a uma lista original de linhas com validação estrita.
    """
    diff_lines = diff_str.splitlines(keepends=True)
    result = list(original)
    
    # Índice atual para simular varredura sequencial baseada em hunks
    i = 0
    in_hunk = False
    
    for line in diff_lines:
        # Ignorar cabeçalhos de arquivo do Unified Diff
        if line.startswith("---") or line.startswith("+++"):
            continue
        if line.startswith("@@"):
            in_hunk = True
            continue
            
        if not in_hunk:
            continue
            
        if not line:
            continue
            
        op = line[0]
        content = line[1:]
        
        if op == ' ':
            # Linha de contexto: verifica se bate com a original no índice i
            if i < len(result) and result[i] == content:
                i += 1
            else:
                # Tenta buscar localmente se o índice exato falhar por deslocamento menor
                found = False
                for search_idx in range(i, min(i + 5, len(result))):
                    if result[search_idx] == content:
                        i = search_idx + 1
                        found = True
                        break
                if not found:
                    raise ValueError(f"Contexto inválido: linha '{content.strip()}' esperada mas não encontrada.")
        elif op == '-':
            # Linha de remoção
            if i < len(result) and result[i] == content:
                result.pop(i)
            else:
                found = False
                for search_idx in range(i, min(i + 5, len(result))):
                    if result[search_idx] == content:
                        result.pop(search_idx)
                        found = True
                        break
                if not found:
                    raise ValueError(f"Contexto inválido: linha '{content.strip()}' não encontrada para remoção.")
        elif op == '+':
            # Linha de inserção
            result.insert(i, content)
            i += 1
            
    return result

# --- TESTES AUTOMATIZADOS (Testador) ---

def run_tests():
    print("Executando testes corrigidos do Motor de Diff de Myers...")
    
    # Teste 1: Arquivos idênticos
    a = ["linha 1\n", "linha 2\n"]
    b = ["linha 1\n", "linha 2\n"]
    diff = generate_unified_diff(a, b)
    print(f"Teste 1 (Idênticos) gerado com sucesso. Tamanho diff: {len(diff)}")

    # Teste 2: Inserções e Deleções
    a = ["apple\n", "banana\n", "cherry\n"]
    b = ["apple\n", "blueberry\n", "cherry\n", "date\n"]
    script = myers_diff(a, b)
    assert ('-', 'banana\n') in script, "Deveria remover banana"
    assert ('+', 'blueberry\n') in script, "Deveria adicionar blueberry"
    assert ('+', 'date\n') in script, "Deveria adicionar date"
    print("Teste 2 (SES Myers) passou com 100% de asserções corretas.")

    # Teste 3: Geração e Aplicação de Patch com fidelidade total
    diff_str = generate_unified_diff(a, b, "orig.txt", "new.txt")
    reconstructed = apply_patch(a, diff_str)
    
    assert reconstructed == b, f"Reconstrução falhou. Esperado {b}, obtido {reconstructed}"
    print("Teste 3 (Aplicação de Patch) executado com 100% de fidelidade.")

    print("TODOS OS TESTES PASSARAM COM CÓDIGO 0.")

if __name__ == "__main__":
    run_tests()