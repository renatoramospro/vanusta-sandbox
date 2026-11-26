; Assembly x86-64 usando AVX2 para soma de vetores de floats (8 floats por instrução)
; Correções obrigatórias:
; 1. Validação de entrada: N > 0 e ponteiros não nulos.
; 2. Segurança do loop vetorial: Garantir que RCX >= 8 antes de executar o bloco SIMD.
; 3. Prática de ABI: Prologo/Epilogo para preservar registradores callee-saved (ex: R12-R15).
; 4. Sintaxe: Usar registradores válidos (e.g., RDI, RSI, RDX para argumentos, não R1).

    ; --- PROLOGO: Preservação de registradores callee-saved ---
    ; Assumindo que R12, R13, R14, R15 são usados e precisam ser preservados
    push r12
    push r13
    push r14
    push r15

    ; --- VALIDAÇÃO DE ENTRADA ---
    ; RDI=A_ptr, RSI=B_ptr, RDX=C_ptr, RCX=N
    cmp rcx, 0
    jle .loop_end_error ; N <= 0
    cmp rdi, 0
    je .loop_end_error ; A_ptr == NULL
    cmp rsi, 0
    je .loop_end_error ; B_ptr == NULL
    cmp rdx, 0
    je .loop_end_error ; C_ptr == NULL

    mov r8, rdi      ; R8 = A_ptr
    mov r9, rsi      ; R9 = B_ptr
    mov r10, rdx     ; R10 = C_ptr

    ; --- Fase 1: Processamento Vetorial (Múltiplos de 8) ---
    mov r11, 8       ; R11 = 8 (Elementos por iteração)

.loop_vector:
    ; CORREÇÃO 2: Verificar se restam pelo menos 8 elementos antes de usar SIMD
    cmp rcx, 8
    jl .loop_remainder ; Se RCX < 8, pula para o loop de limpeza

    ; 1. Carregar 8 floats de A (32 bytes)
    vmovups ymm0, [r8]
    ; 2. Carregar 8 floats de B (32 bytes)
    vmovups ymm1, [r9]
    ; 3. Somar: ymm0 = ymm0 + ymm1
    vaddps ymm0, ymm1
    ; 4. Armazenar 8 floats em C (32 bytes)
    vmovups [r10], ymm0

    ; 5. Avançar ponteiros e contador
    add r8, 32       ; A_ptr += 32 bytes
    add r9, 32       ; B_ptr += 32 bytes
    add r10, 32      ; C_ptr += 32 bytes
    sub rcx, r11     ; N -= 8

    jmp .loop_vector

.loop_remainder:
    ; --- Fase 2: Loop de Limpeza (Remainder Loop) ---
    cmp rcx, 0
    je .loop_end

.loop_cleanup:
    ; Usa instruções scalar (não SIMD)
    ; 1. Carregar float de A
    movss xmm0, [r8]
    ; 2. Carregar float de B
    movss xmm1, [r9]
    ; 3. Somar
    addss xmm0, xmm1
    ; 4. Armazenar float em C
    movss [r10], xmm0

    ; 5. Avançar ponteiros e contador (4 bytes por float)
    add r8, 4
    add r9, 4
    add r10, 4
    sub rcx, 1

    jmp .loop_cleanup

.loop_end:
    ; --- EPILOGO: Restauração de registradores ---
    pop r15
    pop r14
    pop r13
    pop r12
    ret

.loop_end_error:
    ; Em caso de erro de validação (N<=0 ou ponteiro nulo), retorna um código de erro (e.g., -1)
    ; Para simplicidade da missão, apenas retorna, mas em produção, um erro deve ser propagado.
    ; Aqui, assumimos que o chamador trata o retorno sem dados válidos.
    pop r15
    pop r14
    pop r13
    pop r12
    ret