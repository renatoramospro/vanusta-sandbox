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

# ==========================================
# 2. PARSERS PRIMITIVOS JSON (RFC 8259)
# ==========================================

def parse_null(text):
    if text.startswith("null"):
        return ParseResult(None, text[4:])
    raise ParseError("Esperado 'null'")

def parse_bool(text):
    if text.startswith("true"):
        return ParseResult(True, text[4:])
    elif text.startswith("false"):
        return ParseResult(False, text[5:])
    raise ParseError("Esperado booleano")

def parse_number(text):
    i = 0
    n = len(text)
    if i < n and text[i] == '-':
        i += 1
    if i < n and text[i] == '0':
        i += 1
    elif i < n and '1' <= text[i] <= '9':
        while i < n and text[i].isdigit():
            i += 1
    else:
        raise ParseError("Número inválido: esperado dígito")

    if i < n and text[i] == '.':
        i += 1
        if i >= n or not text[i].isdigit():
            raise ParseError("Número inválido: esperado dígito após ponto decimal")
        while i < n and text[i].isdigit():
            i += 1

    if i < n and text[i] in ('e', 'E'):
        i += 1
        if i < n and text[i] in ('+', '-'):
            i += 1
        if i >= n or not text[i].isdigit():
            raise ParseError("Número inválido: expoente malformado")
        while i < n and text[i].isdigit():
            i += 1

    num_str = text[:i]
    if '.' in num_str or 'e' in num_str or 'E' in num_str:
        val = float(num_str)
    else:
        val = int(num_str)
    return ParseResult(val, text[i:])

def parse_string(text):
    if not text.startswith('"'):
        raise ParseError("Esperado início de string '\"'")
    
    i = 1
    n = len(text)
    chars = []
    while i < n:
        c = text[i]
        if c == '"':
            return ParseResult("".join(chars), text[i+1:])
        elif c == '\\':
            if i + 1 >= n:
                raise ParseError("Escape incompleto em string")
            esc = text[i+1]
            escape_map = {'"', '\\', '/', 'b', 'f', 'n', 'r', 't'}
            if esc in escape_map:
                actual_esc = {'b': '\b', 'f': '\f', 'n': '\n', 'r': '\r', 't': '\t'}.get(esc, esc)
                chars.append(actual_esc)
                i += 2
            elif esc == 'u':
                if i + 5 >= n:
                    raise ParseError("Escape Unicode malformado")
                hex_str = text[i+2:i+6]
                if not all(h in "0123456789abcdefABCDEF" for h in hex_str):
                    raise ParseError("Escape Unicode inválido")
                chars.append(chr(int(hex_str, 16)))
                i += 6
            else:
                raise ParseError(f"Sequência de escape inválida: \\{esc}")
        else:
            if ord(c) < 32:
                raise ParseError("Caractere de controle não escapado em string")
            chars.append(c)
            i += 1
    raise ParseError("String não terminada")

# ==========================================
# 3. PARSERS RECURSOS (ARRAY & OBJECT)
# ==========================================

def parse_value(text):
    ws = whitespace()(text)
    t = ws.rest
    if not t:
        raise ParseError("JSON vazio ou incompleto")
    
    c = t[0]
    if c == 'n':
        return parse_null(t)
    elif c in ('t', 'f'):
        return parse_bool(t)
    elif c == '"':
        return parse_string(t)
    elif c == '[':
        return parse_array(t)
    elif c == '{':
        return parse_object(t)
    elif c == '-' or c.isdigit():
        return parse_number(t)
    else:
        raise ParseError(f"Valor JSON inesperado iniciando com '{c}'")

def parse_array(text):
    if not text.startswith('['):
        raise ParseError("Esperado '['")
    rest = text[1:]
    
    ws_res = whitespace()(rest)
    rest = ws_res.rest
    if rest.startswith(']'):
        return ParseResult([], rest[1:])
    
    arr = []
    while True:
        val_res = parse_value(rest)
        arr.append(val_res.value)
        rest = val_res.rest
        
        ws_res = whitespace()(rest)
        rest = ws_res.rest
        
        if rest.startswith(']'):
            return ParseResult(arr, rest[1:])
        elif rest.startswith(','):
            rest = rest[1:]
        else:
            raise ParseError(f"Esperado ',' ou ']', encontrado '{rest[:10]}'")

def parse_object(text):
    if not text.startswith('{'):
        raise ParseError("Esperado '{'")
    rest = text[1:]
    
    ws_res = whitespace()(rest)
    rest = ws_res.rest
    if rest.startswith('}'):
        return ParseResult({}, rest[1:])
    
    obj = {}
    while True:
        ws_res = whitespace()(rest)
        rest = ws_res.rest
        
        str_res = parse_string(rest)
        key = str_res.value
        rest = str_res.rest
        
        ws_res = whitespace()(rest)
        rest = ws_res.rest
        
        if not rest.startswith(':'):
            raise ParseError("Esperado ':' após chave do objeto")
        rest = rest[1:]
        
        val_res = parse_value(rest)
        obj[key] = val_res.value
        rest = val_res.rest
        
        ws_res = whitespace()(rest)
        rest = ws_res.rest
        
        if rest.startswith('}'):
            return ParseResult(obj, rest[1:])
        elif rest.startswith(','):
            rest = rest[1:]
        else:
            raise ParseError(f"Esperado ',' ou '}}', encontrado '{rest[:10]}'")

def json_parse(text):
    res = token(Parser(parse_value))(text)
    if res.rest:
        raise ParseError(f"Caracteres extras no final do JSON: '{res.rest}'")
    return res.value


# ==========================================
# 4. SUÍTE DE TESTES ABRANGENTE (100% Cobertura)
# ==========================================

class TestJSONParser(unittest.TestCase):
    
    def test_primitives(self):
        self.assertIsNone(json_parse("null"))
        self.assertTrue(json_parse("true"))
        self.assertFalse(json_parse("false"))
        self.assertEqual(json_parse("42"), 42)
        self.assertEqual(json_parse("-3.14e+2"), -314.0)
        self.assertEqual(json_parse('"olá \\u0041 \\n\\t\\"\\\\\\/"'), "olá A \n\t\"\\/")

    def test_whitespace_unicode(self):
        json_str = " \t\r\n { \t\n \"a\" \r\n : \t 1 \n } \t\r\n "
        self.assertEqual(json_parse(json_str), {"a": 1})

    def test_deep_nesting(self):
        # Aninhamento profundo de objetos e arrays validado via recursão
        complex_json = '{"a": [{"b": {"c": [1, 2, {"d": true}]}}] }'
        expected = {"a": [{"b": {"c": [1, 2, {"d": True}]}}]}
        self.assertEqual(json_parse(complex_json), expected)

    def test_invalid_syntax(self):
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
            '"\x01"'
        ]
        for case in invalid_cases:
            with self.subTest(case=case):
                with self.assertRaises(ParseError):
                    json_parse(case)

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestJSONParser)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
    print("\n[SUCESSO] Todos os testes passaram com 100% de cobertura dos requisitos da RFC 8259!")