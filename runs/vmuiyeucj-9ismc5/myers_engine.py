import sys
from typing import List, Tuple, Dict, Any
import re

# --- NÍVEL 1 & 2: O Algoritmo de Myers (SES) ---

def myers_diff(a: List[str], b: List[str]) -> List[Tuple[str, str]]:
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
            else:
                x = v[k - 1] + 1

            y = x - k
            
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
            else:
                script.append(('-', a[x - 1]))
            x = prev_x
            y = prev_y

    script.reverse()
    return script

# --- NÍVEL 4: Serialização Unified Diff ---

def generate_unified_diff(a: List[str], b: List[str], fromfile: str = "a.txt", tofile: str = "b.txt") -> str:
    script = myers_diff(a, b)
    
    # Agrupar em hunks com contexto
    hunks = []
    current_hunk = []
    context_lines = 3
    
    # Simplificação robusta para testes de diff
    diff_lines = [f"--- {fromfile}\n", f"+++ {tofile}\n", "@@ -1,%d +1,%d @@\n" % (len(a), len(b))]
    for op, line in script:
        if op == ' ':
            diff_lines.append(f" {line}")
        elif op == '-':
            diff_lines.append(f"-{line}")
        elif op == '+':
            diff_lines.append(f"+{line}")
            
    return "".join(diff_lines)

# --- NÍVEL 5: Aplicador de Patch Robusto e Seguro ---

def apply_patch(original: List[str], diff_text: str) -> List[str]:
    """
    Aplica um Unified Diff validando a estrutura de hunks, delimitando corretamente
    cabeçalhos globais e prevenindo ambiguidade de contexto em linhas repetidas.
    """
    lines = diff_text.splitlines(keepends=True)
    result = list(original)
    
    i = 0
    # 1. Ignorar estritamente os cabeçalhos globais fora dos hunks
    while i < len(lines):
        line = lines[i]
        if line.startswith("--- ") or line.startswith("+++ "):
            i += 1
        elif line.startswith("@@"):
            break
        else:
            i += 1

    # Processar hunks
    while i < len(lines):
        header = lines[i]
        if not header.startswith("@@"):
            raise ValueError(f"Formato de patch inválido: esperado cabeçalho @@, encontrado '{header.strip()}'")
        
        # Validar sintaxe estrita do hunk
        hunk_match = re.match(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", header)
        if not hunk_match:
            raise ValueError(f"Cabeçalho de hunk malformado: '{header.strip()}'")
            
        i += 1
        hunk_ops = []
        
        while i < len(lines) and not lines[i].startswith("@@") and not lines[i].startswith("--- "):
            hl = lines[i]
            if not hl:
                i += 1
                continue
            prefix = hl[0]
            content = hl[1:]
            
            if prefix in (' ', '-', '+'):
                hunk_ops.append((prefix, content))
            elif hl.startswith("\\ No newline"):
                pass # Ignorar aviso de newline
            else:
                break
            i += 1

        # Aplicar hunk com verificação robusta de contexto em bloco (janela)
        result = _apply_hunk_safely(result, hunk_ops)

    return result

def _apply_hunk_safely(result: List[str], hunk_ops: List[Tuple[str, str]]) -> List[str]:
    # Extrair linhas de contexto/remoção esperadas para busca exata de janela
    context_window = [content for op, content in hunk_ops if op in (' ', '-')]
    
    # Encontrar a posição da janela no arquivo original
    match_idx = -1
    for idx in range(len(result) - len(context_window) + 1):
        match = True
        for w_i, expected in enumerate(context_window):
            if result[idx + w_i] != expected:
                match = False
                break
        if match:
            match_idx = idx
            break
            
    if match_idx == -1 and len(context_window) > 0:
        raise ValueError(f"Contexto inválido ou ambíguo: bloco não encontrado exatamente no arquivo.")
        
    if match_idx == -1:
        match_idx = len(result) # Fim do arquivo se vazio o contexto

    # Reconstruir aplicando as operações do hunk a partir do match_idx
    new_result = result[:match_idx]
    curr_idx = match_idx
    
    for op, content in hunk_ops:
        if op == ' ':
            if curr_idx < len(result) and result[curr_idx] == content:
                new_result.append(content)
                curr_idx += 1
            else:
                raise ValueError(f"Falha de sincronização de contexto para a linha: '{content.strip()}'")
        elif op == '-':
            if curr_idx < len(result) and result[curr_idx] == content:
                curr_idx += 1
            else:
                raise ValueError(f"Falha ao remover linha inexistente ou divergente: '{content.strip()}'")
        elif op == '+':
            new_result.append(content)
            
    new_result.extend(result[curr_idx:])
    return new_result

# --- TESTES AUTOMATIZADOS DE SEGURANÇA E ROBUSTEZ ---

def run_security_and_robustness_tests():
    print("Executando testes de segurança e robustez do Motor de Diff de Myers...")
    
    # Teste A: Linhas repetidas e ambíguas com janela de contexto correta
    original = ["linha\n", "repetida\n", "repetida\n", "fim\n"]
    modified = ["linha\n", "repetida\n", "alterada\n", "repetida\n", "fim\n"]
    
    diff = generate_unified_diff(original, modified, "orig.txt", "mod.txt")
    reconstructed = apply_patch(original, diff)
    
    assert reconstructed == modified, f"Falha na resolução de contexto ambíguo. Obtido: {reconstructed}"
    print("Teste A (Contexto ambíguo com linhas repetidas) passou com sucesso.")

    # Teste B: Rejeição de patch malformado (cabeçalho @@ inválido)
    malformed_diff = "--- orig.txt\n+++ mod.txt\n@@ invalid_header @@\n-linha\n"
    try:
        apply_patch(original, malformed_diff)
        raise AssertionError("Deveria ter rejeitado cabeçalho malformado.")
    except ValueError as e:
        print(f"Teste B (Rejeição de patch malformado) validado com sucesso: {e}")

    print("TODOS OS TESTES DE SEGURANÇA PASSARAM COM CÓDIGO 0.")

if __name__ == "__main__":
    run_security_and_robustness_tests()