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

def parse_literal():
    def parse(text):
        if text.startswith("true"):
            return ParseResult(True, text[4:])
        if text.startswith("false"):
            return ParseResult(False, text[5:])
        if text.startswith("null"):
            return ParseResult(None, text[4:])
        raise ParseError(f"Literal desconhecido em: {text[:10]}")
    return Parser(parse)

def parse_number():
    def parse(text):
        i = 0
        n = len(text)
        if i < n and text[i] == '-':
            i += 1
        if i >= n or not text[i].isdigit():
            raise ParseError("Número inválido: esperado dígito")
        
        if text[i] == '0':
            i += 1
        else:
            while i < n and text[i].isdigit():
                i += 1
                
        if i < n and text[i] == '.':
            i += 1
            if i >= n or not text[i].isdigit():
                raise ParseError("Número inválido: dígito esperado após ponto decimal")
            while i < n and text[i].isdigit():
                i += 1
                
        if i < n and text[i] in ('e', 'E'):
            i += 1
            if i < n and text[i] in ('+', '-'):
                i += 1
            if i >= n or not text[i].isdigit():
                raise ParseError("Número inválido: expoente obrigatório")
            while i < n and text[i].isdigit():
                i += 1
                
        num_str = text[:i]
        try:
            if '.' in num_str or 'e' in num_str or 'E' in num_str:
                val = float(num_str)
            else:
                val = int(num_str)
        except ValueError as e:
            raise ParseError(f"Erro ao converter número '{num_str}': {e}")
            
        return ParseResult(val, text[i:])
    return Parser(parse)

def parse_string_raw():
    def parse(text):
        if not text.startswith('"'):
            raise ParseError("Esperada string iniciada por aspas")
        i = 1
        n = len(text)
        chars = []
        while i < n:
            c = text[i]
            if c == '"':
                return ParseResult("".join(chars), text[i+1:])
            elif c == '\\':
                i += 1
                if i >= n:
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
                    if i + 4 >= n:
                        raise ParseError("Sequência \\u incompleta")
                    hex_str = text[i+1:i+5]
                    try:
                        code_point = int(hex_str, 16)
                    except ValueError:
                        raise ParseError(f"Sequência \\u inválida: {hex_str}")
                    i += 4
                    
                    # Tratamento rigoroso de Surrogate Pairs (RFC 8259 / Unicode)
                    if 0xD800 <= code_point <= 0xDBFF:
                        # High surrogate, procurar low surrogate imediato (\uDC00-\uDFFF)
                        if i + 6 < n and text[i+1:i+3] == '\\u':
                            low_hex = text[i+3:i+7]
                            try:
                                low_code = int(low_hex, 16)
                                if 0xDC00 <= low_code <= 0xDFFF:
                                    code_point = 0x10000 + ((code_point - 0xD800) << 10) + (low_code - 0xDC00)
                                    i += 6
                            except ValueError:
                                pass
                    chars.append(chr(code_point))
                else:
                    raise ParseError(f"Escape desconhecido: \\{esc}")
            else:
                if ord(c) < 32:
                    raise ParseError(f"Caractere de controle não escapado: {hex(ord(c))}")
                chars.append(c)
            i += 1
        raise ParseError("String não terminada")
    return Parser(parse)

def json_value(depth=0, max_depth=100):
    if depth > max_depth:
        raise ParseError("Estouro de pilha: aninhamento JSON muito profundo")
    def parse(text):
        # Tenta parsear qualquer tipo JSON válido
        ws = whitespace()(text)
        t = ws.rest
        if not t:
            raise ParseError("Entrada vazia para valor JSON")
        
        if t.startswith('"'):
            return parse_string_raw()(t)
        elif t[0] in '0123456789-':
            return parse_number()(t)
        elif t.startswith('true') or t.startswith('false') or t.startswith('null'):
            return parse_literal()(t)
        elif t.startswith('['):
            return parse_array(depth, max_depth)(t)
        elif t.startswith('{'):
            return parse_object(depth, max_depth)(t)
        else:
            raise ParseError(f"Valor JSON inválido em: {t[:10]}")
    return Parser(parse)

def parse_array(depth, max_depth):
    def parse(text):
        if not text.startswith('['):
            raise ParseError("Esperado '['")
        rest = text[1:]
        res_ws = whitespace()(rest)
        rest = res_ws.rest
        
        if rest.startswith(']'):
            return ParseResult([], rest[1:])
            
        elements = []
        while True:
            val_res = json_value(depth + 1, max_depth)(rest)
            elements.append(val_res.value)
            rest = val_res.rest
            
            res_ws = whitespace()(rest)
            rest = res_ws.rest
            
            if rest.startswith(']'):
                return ParseResult(elements, rest[1:])
            elif rest.startswith(','):
                rest = rest[1:]
                res_ws = whitespace()(rest)
                rest = res_ws.rest
                # Rejeitar trailing commas estritamente conforme RFC 8259
                if rest.startswith(']'):
                    raise ParseError("Vírgula sobrando (trailing comma) não permitida em arrays")
            else:
                raise ParseError(f"Esperado ',' ou ']', encontrado: {rest[:10]}")
    return Parser(parse)

def parse_object(depth, max_depth):
    def parse(text):
        if not text.startswith('{'):
            raise ParseError("Esperado '{'")
        rest = text[1:]
        res_ws = whitespace()(rest)
        rest = res_ws.rest
        
        if rest.startswith('}'):
            return ParseResult({}, rest[1:])
            
        obj = {}
        while True:
            res_ws = whitespace()(rest)
            rest = res_ws.rest
            if not rest.startswith('"'):
                raise ParseError("Esperada string como chave do objeto")
            
            key_res = parse_string_raw()(rest)
            key = key_res.value
            rest = key_res.rest
            
            res_ws = whitespace()(rest)
            rest = res_ws.rest
            if not rest.startswith(':'):
                raise ParseError("Esperado ':' após chave do objeto")
            rest = rest[1:]
            
            val_res = json_value(depth + 1, max_depth)(rest)
            obj[key] = val_res.value
            rest = val_res.rest
            
            res_ws = whitespace()(rest)
            rest = res_ws.rest
            
            if rest.startswith('}'):
                return ParseResult(obj, rest[1:])
            elif rest.startswith(','):
                rest = rest[1:]
                res_ws = whitespace()(rest)
                rest = res_ws.rest
                # Rejeitar trailing commas em objetos
                if rest.startswith('}'):
                    raise ParseError("Vírgula sobrando (trailing comma) não permitida em objetos")
            else:
                raise ParseError(f"Esperado ',' ou '}', encontrado: {rest[:10]}")
    return Parser(parse)

def json_parse(text):
    res = token(json_value(0, max_depth=50))(text)
    if res.rest:
        raise ParseError(f"Caracteres extras no final da string JSON: {res.rest[:10]}")
    return res.value

# ==========================================
# 2. SUÍTE DE TESTES E VALIDAÇÃO DE COBERTURA
# ==========================================

class TestJSONParser(unittest.TestCase):
    
    def test_primitives_and_scientific_numbers(self):
        self.assertEqual(json_parse("true"), True)
        self.assertEqual(json_parse("false"), False)
        self.assertEqual(json_parse("null"), None)
        self.assertEqual(json_parse("42"), 42)
        self.assertEqual(json_parse("-3.14e+2"), -314.0)
        self.assertEqual(json_parse("[1.23e-10, -0.00045, 1e+5]"), [1.23e-10, -0.00045, 100000.0])

    def test_unicode_and_surrogate_pairs(self):
        # Escape Unicode simples e Surrogate Pair (ex: emoji 𝄞 U+1D11E -> \uD834\uDD1E)
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
            '"\x01"' # Caractere de controle não escapado
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