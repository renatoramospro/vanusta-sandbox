import unittest
import sys

# ==========================================
# 1. NÚCLEO DO PARSER COMBINATOR
# ==========================================

class ParseResult:
    def __init__(self, value, rest):
        self.value = value
        self.rest = rest
        self.success = True

    def __repr__(self):
        return f"Success({repr(self.value)}, rest={repr(self.rest)})"

class ParseError(Exception):
    pass

class Parser:
    def __init__(self, parse_fn):
        self.parse_fn = parse_fn

    def __call__(self, text):
        return self.parse_fn(text)

def whitespace():
    def parse(text):
        i = 0
        # RFC 8259 define whitespace como: espaço (U+0020), tabulação (U+0009), 
        # retorno de carro (U+000D) e alimentação de linha (U+000A)
        while i < len(text) and text[i] in " \t\n\r":
            i += 1
        return ParseResult(None, text[i:])
    return Parser(parse)

def token(p):
    def parse(text):
        ws1 = whitespace()(text)
        res = p(ws1.rest)
        ws2 = whitespace()(res.rest)
        return ParseResult(res.value, ws2.rest)
    return Parser(parse)

def lit_string(expected):
    def parse(text):
        if text.startswith(expected):
            return ParseResult(expected, text[len(expected):])
        raise ParseError(f"Esperado literal '{expected}', encontrado '{text[:10]}'")
    return Parser(parse)

def parse_null(text):
    res = lit_string("null")(text)
    return ParseResult(None, res.rest)

def parse_bool(text):
    try:
        res = lit_string("true")(text)
        return ParseResult(True, res.rest)
    except ParseError:
        res = lit_string("false")(text)
        return ParseResult(False, res.rest)

def parse_number(text):
    i = 0
    if i < len(text) and text[i] == '-':
        i += 1
    
    if i >= len(text):
        raise ParseError("Número incompleto")
    
    if text[i] == '0':
        i += 1
    elif '1' <= text[i] <= '9':
        while i < len(text) and text[i].isdigit():
            i += 1
    else:
        raise ParseError(f"Caractere inválido no início do número: {text[i]}")

    # Fração
    if i < len(text) and text[i] == '.':
        i += 1
        if i >= len(text) or not text[i].isdigit():
            raise ParseError("Dígitos esperados após o ponto decimal")
        while i < len(text) and text[i].isdigit():
            i += 1

    # Expoente
    if i < len(text) and text[i] in 'eE':
        i += 1
        if i < len(text) and text[i] in '+-':
            i += 1
        if i >= len(text) or not text[i].isdigit():
            raise ParseError("Dígitos esperados no expoente")
        while i < len(text) and text[i].isdigit():
            i += 1

    num_str = text[:i]
    rest = text[i:]
    try:
        if '.' in num_str or 'e' in num_str or 'E' in num_str:
            val = float(num_str)
        else:
            val = int(num_str)
        return ParseResult(val, rest)
    except ValueError as e:
        raise ParseError(f"Número inválido: {num_str}") from e

def parse_string(text):
    if not text.startswith('"'):
        raise ParseError("String deve iniciar com aspas")
    
    i = 1
    chars = []
    while i < len(text):
        c = text[i]
        if c == '"':
            # Fim da string
            return ParseResult("".join(chars), text[i+1:])
        elif c == '\\':
            i += 1
            if i >= len(text):
                raise ParseError("Escape Unicode/caractere incompleto")
            esc = text[i]
            if esc == '"': chars.append('"')
            elif esc == '\\': chars.append('\\')
            elif esc == '/': chars.append('/')
            elif esc == 'b': chars.append('\b')
            elif esc == 'f': chars.append('\f')
            elif esc == 'n': chars.append('\n')
            elif esc == 'r': chars.append('\r')
            elif esc == 't': chars.append('\t')
            elif esc == 'u':
                if i + 4 >= len(text):
                    raise ParseError("Sequência \\u incompleta")
                hex_str = text[i+1:i+5]
                if not all(h in "0123456789abcdefABCDEF" for h in hex_str):
                    raise ParseError(f"Sequência \\u inválida: {hex_str}")
                code_point = int(hex_str, 16)
                i += 4
                
                # Tratamento de Surrogate Pairs (\uD800-\uDBFF seguida de \uDC00-\uDFFF)
                if 0xD800 <= code_point <= 0xDBFF:
                    if i + 6 < len(text) and text[i+1:i+3] == '\\u':
                        hex_str2 = text[i+3:i+7]
                        if all(h in "0123456789abcdefABCDEF" for h in hex_str2):
                            cp2 = int(hex_str2, 16)
                            if 0xDC00 <= cp2 <= 0xDFFF:
                                code_point = 0x10000 + ((code_point - 0xD800) << 10) + (cp2 - 0xDC00)
                                i += 6
                chars.append(chr(code_point))
            else:
                raise ParseError(f"Escape inválido: \\{esc}")
        else:
            # Rejeita caracteres de controle não escapados (< 0x20)
            if ord(c) < 0x20:
                raise ParseError(f"Caractere de controle não escapado: {repr(c)}")
            chars.append(c)
        i += 1
    raise ParseError("String não terminada")

def parse_json_value(text, depth=0, max_depth=50):
    if depth > max_depth:
        raise ParseError(f"Profundidade máxima de aninhamento ({max_depth}) excedida (proteção contra estouro de pilha)")
    
    ws = whitespace()(text)
    t = ws.rest
    if not t:
        raise ParseError("Entrada vazia ou incompleta")

    c = t[0]
    if c == 'n':
        res = parse_null(t)
        return ParseResult(res.value, res.rest)
    elif c == 't' or c == 'f':
        res = parse_bool(t)
        return ParseResult(res.value, res.rest)
    elif c == '"':
        res = parse_string(t)
        return ParseResult(res.value, res.rest)
    elif c == '-' or c.isdigit():
        res = parse_number(t)
        return ParseResult(res.value, res.rest)
    elif c == '[':
        return parse_array(t, depth, max_depth)
    elif c == '{':
        return parse_object(t, depth, max_depth)
    else:
        raise ParseError(f"Valor JSON inesperado iniciando com: {repr(c)}")

def parse_array(text, depth, max_depth):
    # text começa com '['
    rest = text[1:]
    items = []
    
    ws = whitespace()(rest)
    rest = ws.rest
    if rest and rest[0] == ']':
        return ParseResult([], rest[1:])
    
    while True:
        val_res = parse_json_value(rest, depth + 1, max_depth)
        items.append(val_res.value)
        rest = val_res.rest
        
        ws = whitespace()(rest)
        rest = ws.rest
        
        if not rest:
            raise ParseError("Array não fechado")
        
        if rest[0] == ']':
            return ParseResult(items, rest[1:])
        elif rest[0] == ',':
            rest = rest[1:]
            # Verifica trailing comma estrito [1, ]
            ws_check = whitespace()(rest)
            if ws_check.rest and ws_check.rest[0] == ']':
                raise ParseError("Trailing comma não permitido em arrays conforme RFC 8259")
        else:
            raise ParseError(f"Esperado ',' ou ']', encontrado: {rest[:10]}")

def parse_object(text, depth, max_depth):
    # text começa com '{'
    rest = text[1:]
    obj = {}
    
    ws = whitespace()(rest)
    rest = ws.rest
    if rest and rest[0] == '}':
        return ParseResult({}, rest[1:])
    
    while True:
        ws = whitespace()(rest)
        rest = ws.rest
        if not rest or rest[0] != '"':
            raise ParseError("Esperada chave de string no objeto")
        
        key_res = parse_string(rest)
        key = key_res.value
        rest = key_res.rest
        
        ws = whitespace()(rest)
        rest = ws.rest
        if not rest or rest[0] != ':':
            raise ParseError(f"Esperado ':' após chave, encontrado: {rest[:10]}")
        
        rest = rest[1:]
        val_res = parse_json_value(rest, depth + 1, max_depth)
        obj[key] = val_res.value
        rest = val_res.rest
        
        ws = whitespace()(rest)
        rest = ws.rest
        
        if not rest:
            raise ParseError("Objeto não fechado")
        
        if rest[0] == '}':
            return ParseResult(obj, rest[1:])
        elif rest[0] == ',':
            rest = rest[1:]
            # Verifica trailing comma estrito {"a": 1,}
            ws_check = whitespace()(rest)
            if ws_check.rest and ws_check.rest[0] == '}':
                raise ParseError("Trailing comma não permitido em objetos conforme RFC 8259")
        else:
            # Correção crítica do SyntaxError: chaves duplicadas {{}} para literal na f-string
            raise ParseError(f"Esperado ',' ou '}}', encontrado: {rest[:10]}")

def json_parse(text):
    res = token(lambda t: parse_json_value(t))(text)
    if res.rest:
        raise ParseError(f"Caracteres extras encontrados no final do JSON: {repr(res.rest[:20])}")
    return res.value

# ==========================================
# 2. SUÍTE DE TESTES UNITÁRIOS
# ==========================================

class TestJSONParser(unittest.TestCase):

    def test_primitives(self):
        self.assertIsNone(json_parse("null"))
        self.assertTrue(json_parse("true"))
        self.assertFalse(json_parse("false"))
        self.assertEqual(json_parse("123"), 123)
        self.assertEqual(json_parse("-456"), -456)
        self.assertEqual(json_parse("3.14159"), 3.14159)
        self.assertEqual(json_parse("1.5E+2"), 150.0)
        self.assertEqual(json_parse("2.5e-3"), 0.0025)
        self.assertEqual(json_parse('"olá mundo"'), "olá mundo")

    def test_unicode_and_surrogates(self):
        # Escape básico e Surrogate Pair (Musical Symbol G Clef U+1D11E -> \uD834\uDD1E)
        escaped = '"\\u0041 \\uD834\\uDD1E"'
        res = json_parse(escaped)
        self.assertEqual(res, "A 𝄞")

    def test_deep_nesting_and_recursion_limit(self):
        # Aninhamento profundo válido
        complex_json = '{"a": [{"b": {"c": [1, 2, {"d": true}]}}] }'
        expected = {"a": [{"b": {"c": [1, 2, {"d": True}]}}]}
        self.assertEqual(json_parse(complex_json), expected)

        # Aninhamento excessivo para testar proteção contra estouro de pilha
        deep_invalid = "[" * 60 + "]" * 60
        with self.assertRaises(ParseError):
            json_parse(deep_invalid)

    def test_invalid_syntax_cases(self):
        invalid_cases = [
            '{"chave": malformed}',
            '{"chave": "sem fechamento',
            '[1, 2, ]',
            '{"a": 1,}',
            '{"a" 1}',
            'true extra',
            '{"a": 1} extra',
            '-',
            '1.',
            '\\uZZZZ',
            '"\x01"'  # Caractere de controle não escapado
        ]
        for case in invalid_cases:
            with self.subTest(case=case):
                with self.assertRaises(ParseError):
                    json_parse(case)

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestJSONParser)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
    print("\n[SUCESSO] Parser validado contra RFC 8259 com tratamento rigoroso de Surrogate Pairs e Limite de Recursão!")