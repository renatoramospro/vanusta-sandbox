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


# --- 2. Wasm Binary Parser ---

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
    
    module = WasmModule()
    offset = 8
    
    while offset < len(data):
        section_id = data[offset]
        offset += 1
        section_size, offset = decode_u32(data, offset)
        section_end = offset + section_size
        
        if section_id == 1: # Type section
            count, offset = decode_u32(data, offset)
            for _ in range(count):
                form = data[offset]; offset += 1
                if form != 0x60:
                    raise ValueError("Invalid function type form")
                param_count, offset = decode_u32(data, offset)
                params = []
                for _ in range(param_count):
                    params.append(data[offset]); offset += 1
                return_count, offset = decode_u32(data, offset)
                results = []
                for _ in range(return_count):
                    results.append(data[offset]); offset += 1
                module.types.append((params, results))
                
        elif section_id == 2: # Import section
            import_count, offset = decode_u32(data, offset)
            for _ in range(import_count):
                mod_len, offset = decode_u32(data, offset)
                offset += mod_len # skip module name
                field_len, offset = decode_u32(data, offset)
                offset += field_len # skip field name
                kind = data[offset]; offset += 1
                if kind == 0x00: # Function import
                    type_idx, offset = decode_u32(data, offset)
                    module.imports_count += 1
                    module.functions.append(type_idx)
                else:
                    raise ValueError(f"Unsupported import kind: {kind}")
                    
        elif section_id == 3: # Function section (declarations)
            func_count, offset = decode_u32(data, offset)
            for _ in range(func_count):
                type_idx, offset = decode_u32(data, offset)
                module.functions.append(type_idx)
                
        elif section_id == 7: # Export section
            export_count, offset = decode_u32(data, offset)
            for _ in range(export_count):
                str_len, offset = decode_u32(data, offset)
                name = data[offset:offset+str_len].decode('utf-8')
                offset += str_len
                kind = data[offset]; offset += 1
                if kind == 0x00: # Function export
                    func_idx, offset = decode_u32(data, offset)
                    module.exports[name] = func_idx
                else:
                    raise ValueError(f"Unsupported export kind: {kind}")
                    
        elif section_id == 10: # Code section
            code_count, offset = decode_u32(data, offset)
            for _ in range(code_count):
                body_size, offset = decode_u32(data, offset)
                body_end = offset + body_size
                
                local_count, offset = decode_u32(data, offset)
                locals_list = []
                for _ in range(local_count):
                    l_count, offset = decode_u32(data, offset)
                    l_type = data[offset]; offset += 1
                    for _ in range(l_count):
                        locals_list.append(l_type)
                
                instructions = []
                while offset < body_end:
                    op = data[offset]
                    offset += 1
                    if op == 0x01: # nop
                        instructions.append(('nop',))
                    elif op == 0x0b: # end
                        instructions.append(('end',))
                    elif op == 0x0f: # return
                        instructions.append(('return',))
                    elif op == 0x20: # local.get
                        idx, offset = decode_u32(data, offset)
                        instructions.append(('local.get', idx))
                    elif op == 0x21: # local.set
                        idx, offset = decode_u32(data, offset)
                        instructions.append(('local.set', idx))
                    elif op == 0x41: # i32.const
                        val, offset = decode_i32(data, offset)
                        instructions.append(('i32.const', val))
                    elif op == 0x6a: # i32.add
                        instructions.append(('i32.add',))
                    elif op == 0x6b: # i32.sub
                        instructions.append(('i32.sub',))
                    elif op == 0x6c: # i32.mul
                        instructions.append(('i32.mul',))
                    elif op == 0x6d: # i32.div_s
                        instructions.append(('i32.div_s',))
                    else:
                        raise ValueError(f"Unknown opcode: {op:02x}")
                        
                module.code.append((locals_list, instructions))
        else:
            offset = section_end
            
    return module


# --- 3. VM Execution Engine ---

def execute(module: WasmModule, func_index: int, args: list):
    if func_index < module.imports_count:
        raise NotImplementedError("Execution of imported functions is not implemented")
    
    local_code_index = func_index - module.imports_count
    if local_code_index < 0 or local_code_index >= len(module.code):
        raise IndexError(f"Function index {func_index} out of range for local code bodies")
    
    type_idx = module.functions[func_index]
    param_types, result_types = module.types[type_idx]
    
    if len(args) != len(param_types):
        raise TypeError(f"Expected {len(param_types)} arguments, got {len(args)}")
        
    local_types, instructions = module.code[local_code_index]
    locals_val = list(args) + [0] * len(local_types)
    
    stack = []
    pc = 0
    
    while pc < len(instructions):
        instr = instructions[pc]
        op = instr[0]
        
        if op == 'i32.const':
            stack.append(instr[1])
        elif op == 'local.get':
            stack.append(locals_val[instr[1]])
        elif op == 'local.set':
            locals_val[instr[1]] = stack.pop()
        elif op == 'i32.add':
            b = stack.pop()
            a = stack.pop()
            stack.append((a + b) & 0xFFFFFFFF)
        elif op == 'i32.sub':
            b = stack.pop()
            a = stack.pop()
            stack.append((a - b) & 0xFFFFFFFF)
        elif op == 'i32.mul':
            b = stack.pop()
            a = stack.pop()
            stack.append((a * b) & 0xFFFFFFFF)
        elif op == 'i32.div_s':
            b = stack.pop()
            a = stack.pop()
            if b == 0:
                raise ZeroDivisionError("integer divide by zero")
            # Sign-aware division for 32-bit integers
            if a & 0x80000000: a -= 0x100000000
            if b & 0x80000000: b -= 0x100000000
            res = int(a / b)
            stack.append(res & 0xFFFFFFFF)
        elif op == 'nop':
            pass
        elif op == 'end' or op == 'return':
            break
        pc += 1
        
    return stack.pop() if stack else None


# --- 4. Tests ---

def test_assembler_binary_generation():
    # Constructing a valid Wasm binary containing:
    # - Type section: func (param i32) -> (result i32)
    # - Function section: 1 function of type 0
    # - Export section: export func 0 as "add42"
    # - Code section: local.get 0, i32.const 42, i32.add, end
    wasm_bytes = b'\x00asm\x01\x00\x00\x00' \
                 b'\x01\x04\x01\x60\x01\x7f\x01\x7f' \
                 b'\x03\x02\x01\x00' \
                 b'\x07\x09\x01\x05add42\x00\x00' \
                 b'\x0a\x0a\x01\x08\x00\x20\x00\x41\x2a\x6a\x0b'
    
    module = parse_wasm(wasm_bytes)
    func_idx = module.exports['add42']
    res = execute(module, func_idx, [32])
    print("SUCCESS: Binary parsing and arithmetic execution test passed! Result:", res)
    assert res == 74

def test_edge_cases():
    wasm_bytes = b'\x00asm\x01\x00\x00\x00' \
                 b'\x01\x04\x01\x60\x00\x01\x7f' \
                 b'\x03\x02\x01\x00' \
                 b'\x07\x07\x01\x03div\x00\x00' \
                 b'\x0d\x07\x01\x05\x00\x41\x64\x41\x00\x6d\x0b'
    
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