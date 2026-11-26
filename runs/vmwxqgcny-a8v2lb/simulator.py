import numpy as np

# Constantes e Gates
SQRT2_INV = 1.0 / np.sqrt(2.0)
H = SQRT2_INV * np.array([[1, 1], [1, -1]], dtype=complex)
I = np.array([[1, 0], [0, 1]], dtype=complex)

# Matrizes de 2 Qubits (4x4)
# Ordem: Qubit 0 (LSB) \otimes Qubit 1 (MSB)
# Para H no Qubit 0 e I no Qubit 1: U = H \otimes I
U_H_I = np.kron(H, I)

# CNOT (Control Qubit 0, Target Qubit 1)
# |00> -> |00>
# |01> -> |01>
# |10> -> |11>
# |11> -> |10>
U_CNOT = np.array([
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 0, 1], # |10> -> |11> (índice 2 -> 3)
    [0, 0, 1, 0]  # |11> -> |10> (índice 3 -> 2)
], dtype=complex)

def simulate_circuit(initial_state, gates):
    """Aplica gates sequencialmente ao vetor de estado."""
    state = initial_state.copy()
    for gate in gates:
        # Aplicação correta: Produto matricial
        state = np.dot(gate, state)
    return state

# --- Execução do Experimento ---
# Estado inicial |00>
initial_state_00 = np.array([1.0, 0.0, 0.0, 0.0], dtype=complex)

# Circuito: (H \otimes I) -> CNOT
circuit_gates = [U_H_I, U_CNOT]

final_state = simulate_circuit(initial_state_00, circuit_gates)

# 1. Normalização (Verificação de preservação de norma)
norm_final = np.linalg.norm(final_state)
normalized_state = final_state / norm_final

# 2. Resultado teórico esperado: 1/sqrt(2) * [1, 1, 0, 0]
expected_amplitude = 1.0 / np.sqrt(2.0)
expected_state = np.array([expected_amplitude, expected_amplitude, 0.0, 0.0], dtype=complex)

# 3. Verificação de precisão (Erro L2)
error_vector = normalized_state - expected_state
l2_error = np.linalg.norm(error_vector)

print("Vetor de Estado Final (Normalizado):")
print(normalized_state)
print("\nNorma L2 do vetor final:", norm_final)
print("Erro L2 em relação ao teórico:", l2_error)

# Critério de sucesso revisado:
# a) Norma L2 ~ 1.0 (tolerância 1e-9)
# b) Erro L2 vs. Teórico <= 1e-6
success_norm = np.isclose(norm_final, 1.0, atol=1e-9)
success_precision = l2_error <= 1e-6

if success_norm and success_precision:
    print("\nSUCESSO TOTAL: Norma preservada E Erro L2 <= 1e-6.")
else:
    print("\nFALHA: Critério de sucesso não atendido.")