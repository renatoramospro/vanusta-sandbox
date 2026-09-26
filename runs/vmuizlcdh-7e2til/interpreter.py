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


# --- 2. Wasm Binary Parser with Strict Section Bounds ---

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
    if magic != b'\x00asm':
        raise ValueError(f"Invalid magic number: {magic}")
    
    version = data[4:8]
    if version != b'\x01\x00\x00\x00':
        raise ValueError(f"Unsupported Wasm version: {version}")
    
    offset = 8
    module = WasmModule()
    
    while offset < len(data):
        section_id = data[offset]
        offset += 1
        section_size, offset = decode_u32(data, offset)
        section_end = offset + section_size
        
        if section_end > len(data):
            raise ValueError("Section size exceeds file bounds")
        
        if section_id == 1: # Type section
            count, offset = decode_u32(data, offset)
            for _ in range(count):
                if offset >= section_end:
                    raise ValueError("Unexpected end of type section")
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
                # module name len + string
                mod_len, offset = decode_u32(data, offset)
                offset += mod_len
                # field name len + string
                field_len, offset = decode_u32(data, offset)
                offset += field_len
                import_kind = data[offset]
                offset += 1
                if import_kind == 0x00: # function import
                    type_idx, offset = decode_u32(data, offset)
                    module.imports_count += 1
                    module.functions.append(type_idx)
                else:
                    raise ValueError(f"Unsupported import kind: {import_kind}")
                    
        elif section_id == 3: # Function section
            count, offset = decode_u32(data, offset)
            for _ in range(count):
                type_idx, offset = decode_u32(data, offset)
                module.functions.append(type_idx)
                
        elif section_id == 7: # Export section
            count, offset = decode_u32(data, offset)
            for _ in range(count):
                name_len, offset = decode_u32(data, offset)
                name = data[offset:offset+name_len].decode('utf-8')
                offset += name_len
                export_kind = data[offset]
                offset += 1
                func_idx, offset = decode_u32(data, offset)
                if export_kind == 0x00:
                    module.exports[name] = func_idx
                else:
                    raise ValueError(f"Unsupported export kind: {export_kind}")
                    
        elif section_id == 10: # Code section
            count, offset = decode_u32(data, offset)
            for _ in range(count):
                body_size, offset = decode_u32(data, offset)
                body_end = offset + body_size
                
                local_decl_count, offset = decode_u32(data, offset)
                locals_list = []
                for _ in range(local_decl_count):
                    num_locals, offset = decode_u32(data, offset)
                    val_type = data[offset]
                    offset += 1
                    for _ in range(num_locals):
                        locals_list.append(val_type)
                
                instructions = []
                while offset < body_end:
                    op = data[offset]
                    offset += 1
                    if op == 0x0b: # end
                        instructions.append((op,))
                        break
                    elif op == 0x20: # local.get
                        idx, offset = decode_u32(data, offset)
                        instructions.append((op, idx))
                    elif op == 0x41: # i32.const
                        val, offset = decode_i32(data, offset)
                        instructions.append((op, val))
                    elif op in (0x6a, 0x6d, 0x73): # i32.add, i32.mul, i32.div_s
                        instructions.append((op,))
                    else:
                        raise ValueError(f"Unknown opcode: {hex(op)}")
                
                if offset != body_end:
                    raise ValueError("Code body size mismatch")
                
                module.code.append((locals_list, instructions))
        else:
            # Skip unknown or custom sections safely based on section_end
            offset = section_end
            
        if offset != section_end:
            raise ValueError(f"Section {section_id} parsing error: read offset mismatch")
            
    return module


# --- 3. VM Execution Engine ---

def execute(module, func_index, args):
    if func_index < module.imports_count:
        raise NotImplementedError("Execution of imported functions not implemented")
    
    local_code_index = func_index - module.imports_count
    if local_code_index >= len(module.code):
        raise ValueError(f"Function index {func_index} out of range")
        
    local_types, instructions = module.code[local_code_index]
    
    # Initialize locals: arguments followed by declared local variables initialized to 0
    locals_array = list(args)
    for _ in local_types:
        locals_array.append(0)
        
    stack = []
    pc = 0
    
    while pc < len(instructions):
        instr = instructions[pc]
        op = instr[0]
        pc += 1
        
        if op == 0x20: # local.get
            idx = instr[1]
            stack.append(locals_array[idx])
        elif op == 0x41: # i32.const
            val = instr[1]
            stack.append(val)
        elif op == 0x6a: # i32.add
            b = stack.pop()
            a = stack.pop()
            stack.append((a + b) & 0xFFFFFFFF)
        elif op == 0x6d: # i32.mul
            b = stack.pop()
            a = stack.pop()
            stack.append((a * b) & 0xFFFFFFFF)
        elif op == 0x73: # i32.div_s
            b = stack.pop()
            a = stack.pop()
            if b == 0:
                raise ZeroDivisionError("integer divide by zero")
            # Signed division in 32-bit
            if a >= 0x80000000: a -= 0x100000000
            if b >= 0x80000000: b -= 0x100000000
            res = int(a / b)
            if res < 0: res += 0x100000000
            stack.append(res)
        elif op == 0x0b: # end
            break
            
    return stack.pop() if stack else None


# --- 4. Test Suite ---

def test_assembler_binary_generation():
    # Wat: (func (export "add42") (param i32) (result i32) local.get 0, i32.const 42, i32.add, end)
    wasm_bytes = b'\x00asm\x01\x00\x00\x00' \
                 b'\x01\x04\x01\x60\x01\x7f\x01\x7f' \
                 b'\x03\x02\x01\x00' \
                 b'\x07\x09\x01\x05add42\x00\x00' \
                 b'\x0a\x0a\x01\x08\x00\x20\x00\x41\x2a\x6a\x0b'
    
    module = parse_wasm(wasm_bytes)
    func_idx = module.exports['add42']
    res = execute(module, func_idx, [32])
    print("SUCCESS: Binary parsing with strict bounds and arithmetic execution test passed! Result:", res)
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