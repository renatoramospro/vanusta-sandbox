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
        self.types = []      # list of (params, results)
        self.functions = []  # list of type_indices
        self.code = []       # list of (locals, body_instructions)
        self.exports = {}    # name -> func_index

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
                form = data[offset] # 0x60 for func
                offset += 1
                param_count, offset = decode_u32(data, offset)
                params = [data[offset + i] for i in range(param_count)]
                offset += param_count
                return_count, offset = decode_u32(data, offset)
                returns = [data[offset + i] for i in range(return_count)]
                offset += return_count
                module.types.append((params, returns))
                
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
                export_idx, offset = decode_u32(data, offset)
                if export_kind == 0: # Function export
                    module.exports[name] = export_idx
                    
        elif section_id == 10: # Code section
            count, offset = decode_u32(data, offset)
            for _ in range(count):
                body_size, offset = decode_u32(data, offset)
                body_end = offset + body_size
                local_decl_count, offset = decode_u32(data, offset)
                locals_list = []
                for _ in range(local_decl_count):
                    l_count, offset = decode_u32(data, offset)
                    l_type = data[offset]
                    offset += 1
                    for _ in range(l_count):
                        locals_list.append(l_type)
                
                # Instructions until body_end - 1 (expecting 0x0B end)
                instructions = []
                while offset < body_end:
                    op = data[offset]
                    offset += 1
                    if op == 0x20: # local.get
                        idx, offset = decode_u32(data, offset)
                        instructions.append(('local.get', idx))
                    elif op == 0x21: # local.set
                        idx, offset = decode_u32(data, offset)
                        instructions.append(('local.set', idx))
                    elif op == 0x41: # i32.const
                        val, offset = decode_i32(data, offset)
                        instructions.append(('i32.const', val))
                    elif op in (0x6A, 0x6B, 0x6C, 0x6D, 0x02, 0x03, 0x04, 0x0C, 0x0F, 0x1A, 0x1B):
                        # Simple opcodes or structured control opcodes
                        if op == 0x6A: instructions.append(('i32.add',))
                        elif op == 0x6B: instructions.append(('i32.sub',))
                        elif op == 0x6C: instructions.append(('i32.mul',))
                        elif op == 0x6D: instructions.append(('i32.div_s',))
                        elif op == 0x02: # block
                            bt = data[offset]; offset += 1
                            instructions.append(('block', bt))
                        elif op == 0x03: # loop
                            bt = data[offset]; offset += 1
                            instructions.append(('loop', bt))
                        elif op == 0x04: # if
                            bt = data[offset]; offset += 1
                            instructions.append(('if', bt))
                        elif op == 0x0C: # br
                            depth, offset = decode_u32(data, offset)
                            instructions.append(('br', depth))
                        elif op == 0x0F: instructions.append(('return',))
                        elif op == 0x1A: instructions.append(('drop',))
                        elif op == 0x1B: instructions.append(('select',))
                    elif op == 0x0B: # end
                        instructions.append(('end',))
                    else:
                        raise ValueError(f"Unknown opcode: 0x{op:02X}")
                module.code.append((locals_list, instructions))
                offset = body_end
        else:
            offset = section_end
            
    return module


# --- 3. Wasm Virtual Machine Execution Engine ---

class Frame:
    def __init__(self, locals_list, instructions):
        self.locals = locals_list
        self.instructions = instructions
        self.pc = 0

def execute(module, func_index, args):
    type_idx = module.functions[func_index]
    param_types, return_types = module.types[type_idx]
    
    if len(args) != len(param_types):
        raise TypeError(f"Argument count mismatch: expected {len(param_types)}, got {len(args)}")
    
    local_types, instructions = module.code[func_index]
    locals_val = list(args) + [0] * len(local_types)
    
    stack = []
    # Control stack stores: (block_type, start_pc, end_pc, label_stack_depth)
    control_stack = []
    
    pc = 0
    while pc < len(instructions):
        instr = instructions[pc]
        op = instr[0]
        
        if op == 'i32.const':
            stack.append(instr[1])
            pc += 1
        elif op == 'local.get':
            stack.append(locals_val[instr[1]])
            pc += 1
        elif op == 'local.set':
            locals_val[instr[1]] = stack.pop()
            pc += 1
        elif op == 'i32.add':
            b = stack.pop()
            a = stack.pop()
            # 32-bit integer wrapping emulation
            stack.append((a + b) & 0xFFFFFFFF)
            pc += 1
        elif op == 'i32.sub':
            b = stack.pop()
            a = stack.pop()
            stack.append((a - b) & 0xFFFFFFFF)
            pc += 1
        elif op == 'i32.mul':
            b = stack.pop()
            a = stack.pop()
            stack.append((a * b) & 0xFFFFFFFF)
            pc += 1
        elif op == 'i32.div_s':
            b = stack.pop()
            a = stack.pop()
            if b == 0:
                raise ZeroDivisionError("integer divide by zero")
            # Sign adjustment for python division vs trunc_s
            res = int(a / b) if (a < 0) ^ (b < 0) else a // b
            stack.append(res & 0xFFFFFFFF)
            pc += 1
        elif op in ('block', 'loop', 'if'):
            control_stack.append((op, pc, len(stack)))
            pc += 1
        elif op == 'br':
            depth = instr[1]
            # Unwind control stack by depth
            target = control_stack[-(depth + 1)]
            pc = target[1] + 1 # jump after block/loop start
            # Truncate operand stack to block entry level
            stack[:] = stack[:target[2]]
            control_stack[:] = control_stack[:len(control_stack) - (depth + 1)]
        elif op == 'end':
            if control_stack:
                control_stack.pop()
            pc += 1
        elif op == 'return':
            break
        else:
            raise NotImplementedError(f"Instruction not implemented: {op}")
            
    if return_types:
        return stack.pop() if stack else 0
    return None


# --- 4. Automated Tests & Edge Cases Verification ---

def test_assembler_binary_generation():
    # Constructing raw binary for a simple module with function:
    # (func (param i32) (result i32) local.get 0 i32.const 10 i32.add)
    wasm_bytes = b'\x00asm\x01\x00\x00\x00' \
                 b'\x01\x04\x01\x60\x01\x7f\x01\x7f' \
                 b'\x03\x02\x01\x00' \
                 b'\x07\x07\x01\x03add\x00\x00' \
                 b'\x10\x07\x01\x05\x00\x20\x00\x41\x0a\x6a\x0b'
    
    module = parse_wasm(wasm_bytes)
    assert len(module.types) == 1
    assert len(module.functions) == 1
    assert 'add' in module.exports
    
    func_idx = module.exports['add']
    res = execute(module, func_idx, [32])
    assert res == 42
    print("SUCCESS: Binary parsing and arithmetic execution test passed! Result:", res)

def test_edge_cases():
    # Test division by zero exception handling
    wasm_bytes = b'\x00asm\x01\x00\x00\x00' \
                 b'\x01\x04\x01\x60\x00\x01\x7f' \
                 b'\x03\x02\x01\x00' \
                 b'\x07\x07\x01\x03div\x00\x00' \
                 b'\x0d\x07\x01\x05\x00\x41\x64\x41\x00\x6d\x0b' # 100 / 0
    
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