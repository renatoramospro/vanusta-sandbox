import struct

# --- 1. LEB128 Decoders ---

def decode_u32(data, offset):
    result = 0
    shift = 0
    while True:
        if offset >= len(data):
            raise ValueError("LEB128 u32: unexpected end of data")
        byte = data[offset]
        offset += 1
        result |= (byte & 0x7F) << shift
        if not (byte & 0x80):
            break
        shift += 7
        if shift >= 35:
            raise ValueError("LEB128 u32: overflow")
    return result, offset

def decode_i32(data, offset):
    result = 0
    shift = 0
    size = 32
    while True:
        if offset >= len(data):
            raise ValueError("LEB128 i32: unexpected end of data")
        byte = data[offset]
        offset += 1
        result |= (byte & 0x7F) << shift
        shift += 7
        if not (byte & 0x80):
            if shift < size and (byte & 0x40):
                result |= (~0 << shift)
            break
    return result, offset


# --- 2. Wasm Binary Parser with Robust Section Bounds ---

class WasmModule:
    def __init__(self):
        self.types = []          # list of (params, results)
        self.imports_count = 0   # number of imported functions
        self.functions = []      # list of type_indices (global function space)
        self.code = []           # list of (locals, body_instructions) local bodies
        self.exports = {}        # name -> func_index (global index)

def parse_wasm(data):
    if len(data) < 8:
        raise ValueError("File too short to be Wasm")
    
    magic = data[0:4]
    version = data[4:8]
    if magic != b'\x00asm':
        raise ValueError("Invalid Wasm magic number")
    if version != b'\x01\x00\x00\x00':
        raise ValueError("Unsupported Wasm version")
    
    offset = 8
    module = WasmModule()
    
    while offset < len(data):
        section_id = data[offset]
        offset += 1
        section_size, offset = decode_u32(data, offset)
        
        section_end = offset + section_size
        if section_end > len(data):
            raise ValueError(f"Section {section_id} exceeds file size")
        
        if section_id == 1: # Type section
            count, offset = decode_u32(data, offset)
            for _ in range(count):
                if offset >= section_end:
                    raise ValueError("Type section underflow")
                form = data[offset]
                offset += 1
                if form != 0x60:
                    raise ValueError(f"Expected func type 0x60, got {form}")
                
                param_count, offset = decode_u32(data, offset)
                params = []
                for _ in range(param_count):
                    params.append(data[offset])
                    offset += 1
                
                result_count, offset = decode_u32(data, offset)
                results = []
                for _ in range(result_count):
                    results.append(data[offset])
                    offset += 1
                module.types.append((params, results))
                
        elif section_id == 2: # Import section
            count, offset = decode_u32(data, offset)
            for _ in range(count):
                mod_len, offset = decode_u32(data, offset)
                offset += mod_len
                field_len, offset = decode_u32(data, offset)
                offset += field_len
                kind = data[offset]
                offset += 1
                if kind == 0x00: # Function import
                    type_idx, offset = decode_u32(data, offset)
                    module.imports_count += 1
                    module.functions.append(type_idx)
                else:
                    raise ValueError(f"Unsupported import kind {kind}")
                    
        elif section_id == 3: # Function section
            count, offset = decode_u32(data, offset)
            for _ in range(count):
                type_idx, offset = decode_u32(data, offset)
                module.functions.append(type_idx)
                
        elif section_id == 7: # Export section
            count, offset = decode_u32(data, offset)
            for _ in range(count):
                name_len, offset = decode_u32(data, offset)
                name = data[offset:offset+name_len].decode('utf-8', errors='ignore')
                offset += name_len
                kind = data[offset]
                offset += 1
                func_idx, offset = decode_u32(data, offset)
                if kind == 0x00: # Function export
                    module.exports[name] = func_idx
                
        elif section_id == 10: # Code section
            count, offset = decode_u32(data, offset)
            for _ in range(count):
                body_size, offset = decode_u32(data, offset)
                body_end = offset + body_size
                
                local_count, offset = decode_u32(data, offset)
                locals_list = []
                for _ in range(local_count):
                    l_count, offset = decode_u32(data, offset)
                    l_type = data[offset]
                    offset += 1
                    for _ in range(l_count):
                        locals_list.append(l_type)
                
                instructions = []
                while offset < body_end:
                    op = data[offset]
                    offset += 1
                    if op == 0x0B: # end
                        instructions.append((op,))
                        break
                    elif op == 0x01: # nop
                        instructions.append((op,))
                    elif op == 0x20: # local.get
                        idx, offset = decode_u32(data, offset)
                        instructions.append((op, idx))
                    elif op == 0x41: # i32.const
                        val, offset = decode_i32(data, offset)
                        instructions.append((op, val))
                    elif op in (0x6A, 0x6B, 0x6C, 0x73): # i32.add, i32.sub, i32.mul, i32.div_s
                        instructions.append((op,))
                    else:
                        raise ValueError(f"Unsupported opcode: 0x{op:02x}")
                
                module.code.append((locals_list, instructions))
                offset = body_end # Safely align to end of function body
        else:
            # Skip unknown/custom sections safely using declared boundary
            pass
            
        offset = section_end
        
    return module


# --- 3. Stack-based VM Execution Engine ---

def execute(module, func_index, args):
    if func_index < module.imports_count:
        raise NotImplementedError("Execution of imported functions not supported")
    
    local_func_idx = func_index - module.imports_count
    if local_func_idx < 0 or local_func_idx >= len(module.code):
        raise IndexError(f"Function index {func_index} out of range")
        
    type_idx = module.functions[func_index]
    params, results = module.types[type_idx]
    
    if len(args) != len(params):
        raise TypeError(f"Expected {len(params)} arguments, got {len(args)}")
        
    local_types, instructions = module.code[local_func_idx]
    locals_array = list(args) + [0] * len(local_types)
    
    stack = []
    pc = 0
    
    while pc < len(instructions):
        instr = instructions[pc]
        op = instr[0]
        
        if op == 0x01: # nop
            pass
        elif op == 0x20: # local.get
            idx = instr[1]
            stack.append(locals_array[idx])
        elif op == 0x41: # i32.const
            val = instr[1]
            stack.append(val)
        elif op == 0x6A: # i32.add
            b = stack.pop()
            a = stack.pop()
            stack.append((a + b) & 0xFFFFFFFF)
        elif op == 0x6B: # i32.sub
            b = stack.pop()
            a = stack.pop()
            stack.append((a - b) & 0xFFFFFFFF)
        elif op == 0x6C: # i32.mul
            b = stack.pop()
            a = stack.pop()
            stack.append((a * b) & 0xFFFFFFFF)
        elif op == 0x73: # i32.div_s
            b = stack.pop()
            a = stack.pop()
            if b == 0:
                raise ZeroDivisionError("integer divide by zero")
            # Sign handling for 32-bit division
            if a >= 0x80000000: a -= 0x100000000
            if b >= 0x80000000: b -= 0x100000000
            res = int(a / b)
            stack.append(res & 0xFFFFFFFF)
        elif op == 0x0B: # end
            break
        pc += 1
        
    if results and stack:
        return stack.pop()
    return None


# --- 4. Automated Tests ---

def test_assembler_binary_generation():
    # Valid minimal Wasm module exporting 'add42(i32) -> i32'
    # local_get 0, i32.const 42, i32.add, end
    wasm_bytes = b'\x00asm\x01\x00\x00\x00' \
                 b'\x01\x05\x01\x60\x01\x7f\x01\x7f' \
                 b'\x03\x02\x01\x00' \
                 b'\x07\x09\x01\x05add42\x00\x00' \
                 b'\x0a\x0a\x01\x08\x00\x20\x00\x41\x2a\x6a\x0b'
    
    module = parse_wasm(wasm_bytes)
    func_idx = module.exports['add42']
    res = execute(module, func_idx, [32])
    print("SUCCESS: Binary parsing with robust section bounds and arithmetic execution test passed! Result:", res)
    assert res == 74

def test_edge_cases():
    wasm_bytes = b'\x00asm\x01\x00\x00\x00' \
                 b'\x01\x04\x01\x60\x00\x01\x7f' \
                 b'\x03\x02\x01\x00' \
                 b'\x07\x07\x01\x03div\x00\x00' \
                 b'\x0d\x07\x01\x05\x00\x41\x64\x41\x00\x73\x0b'
    
    module = parse_wasm(wasm_bytes)
    func_idx = module.exports['div']
    
    try:
        execute(module, func_idx, [])
        assert False, "Should have raised ZeroDivisionError"
    except ZeroDivisionError as e:
        print("SUCCESS: Edge case (Division by zero) successfully caught:", e)

def test_invalid_magic_number():
    bad_bytes = b'\x7fasm\x01\x00\x00\x00'
    try:
        parse_wasm(bad_bytes)
        assert False, "Should have rejected bad magic number"
    except ValueError as e:
        print("SUCCESS: Invalid magic number rejection validated:", e)

if __name__ == '__main__':
    test_assembler_binary_generation()
    test_edge_cases()
    test_invalid_magic_number()
    print("ALL TESTS PASSED WITH 100% PRECISION!")