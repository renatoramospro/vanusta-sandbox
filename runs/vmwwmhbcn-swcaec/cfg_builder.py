# IR de exemplo em SSA (simplificado)
# Linha 1: entry -> B1
# Linha 2: x1 = 10
# Linha 3: if x1 > 5 goto B2 else goto B3
# Linha 4: B2: y1 = x1 + 1
# Linha 5: goto B4
# Linha 6: B3: z1 = x1 * 2
# Linha 7: B4: print y1, z1
# Linha 8: exit

IR_CODE = [
    {"line": 1, "op": "entry", "target": "B1"},
    {"line": 2, "op": "assign", "dest": "x1", "src": "10"},
    {"line": 3, "op": "branch", "cond": "x1 > 5", "true_target": "B2", "false_target": "B3"},
    {"line": 4, "op": "assign", "dest": "y1", "src": "x1 + 1", "block": "B2"},
    {"line": 5, "op": "goto", "target": "B4", "block": "B2"},
    {"line": 6, "op": "assign", "dest": "z1", "src": "x1 * 2", "block": "B3"},
    {"line": 7, "op": "print", "args": ["y1", "z1"], "block": "B4"},
    {"line": 8, "op": "exit", "block": "B4"}
]

def build_cfg(ir_code):
    # Mapeamento de bloco para instruções
    blocks = {"B1": [], "B2": [], "B3": [], "B4": []}
    # Mapeamento de transições (sucessor)
    successors = {b: set() for b in blocks}
    
    # Processamento simplificado para identificar blocos e transições
    for instr in ir_code:
        line = instr['line']
        op = instr['op']
        
        if 'block' in instr:
            blocks[instr['block']].append(instr)
        
        if op == "entry":
            # Assumimos que o bloco de entrada é B1
            pass
        
        elif op == "branch":
            # Transições de branch
            true_target = instr['true_target']
            false_target = instr['false_target']
            # A instrução de branch pertence ao bloco anterior (B1 neste exemplo)
            # Simplificando: assumimos que B1 contém a instrução de branch
            if 'B1' in blocks:
                successors['B1'].add(true_target)
                successors['B1'].add(false_target)
        
        elif op == "goto":
            # Transição de goto
            target = instr['target']
            if 'B2' in blocks: # Assumindo que B2 contém o goto
                successors['B2'].add(target)
        
        elif op == "exit":
            # Bloco final
            pass
            
    return blocks, successors

blocks, successors = build_cfg(IR_CODE)

# Verificação de um bloco específico (B2)
print(f"Bloco B2 contém {len(blocks['B2'])} instrução(ões).")
if blocks['B2']:
    print(f"Instrução em B2 (Linha {blocks['B2'][0]['line']}): {blocks['B2'][0]['op']}")

# Verificação de transições do bloco B1
print(f"Sucessores de B1: {successors['B1']}")