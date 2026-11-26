; Assembly x86-64 usando AVX2 para soma de vetores de floats (8 floats por instrução)
; Correção: Adição de loop de limpeza (remainder loop) para N não divisível por 8.
; Correção: Consideração conceitual de aliasing (embora checagem dinâmica exija runtime C,
; o Assembly deve ser escrito assumindo que os ponteiros são válidos, mas o loop de limpeza garante
; que os acessos não ultrapassem os limites definidos por N).

; Assumimos que os vetores A, B e C são passados como argumentos de função (e.g., RDI, RSI, RDX)
; RDI = A_ptr, RSI = B_ptr, RDX = C_ptr
; RCX = N (Contador de elementos)

    mov r8, rdi      ; R8 = A_ptr
    mov r9, rsi      ; R9 = B_ptr
    mov r10, rdx     ; R10 = C_ptr
    mov rcx, r1      ; RCX = N (Contador de elementos)

    ; --- Fase 1: Processamento Vetorial (Múltiplos de 8) ---
    mov r11, 8       ; R11 = 8 (Elementos por iteração)
    mov r12, 0       ; R12 = Contador de iterações (N / 8)

.loop_vector:
    cmp rcx, 0
    jle .loop_remainder ; Se N <= 0, pula para o loop de limpeza

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
    ; Processa os N % 8 elementos restantes (0 a 7)
    cmp rcx, 0
    je .loop_end

    ; Loop de limpeza: itera até RCX ser 0
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
    ret