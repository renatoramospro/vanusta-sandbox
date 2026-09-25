class ParseResult:
    def __init__(self, value, rest):
        self.value = value
        self.rest = rest
        self.success = True

    def __repr__(self):
        return f"Success({self.value}, rest={repr(self.rest)})"

class ParseError(Exception):
    pass

class Parser:
    def __init__(self, parse_fn):
        self.parse_fn = parse_fn

    def __call__(self, text):
        return self.parse_fn(text)

    def map(self, fn):
        def parse(text):
            res = self.parse_fn(text)
            if not res.success:
                return res
            res.value = fn(res.value)
            return res
        return Parser(parse)

    def and_then(self, other):
        def parse(text):
            res1 = self.parse_fn(text)
            if not res1.success:
                return res1
            res2 = other(res1.rest)
            if not res2.success:
                return res2
            res2.value = (res1.value, res2.value)
            return res2
        return Parser(parse)

    def or_else(self, other):
        def parse(text):
            try:
                res = self.parse_fn(text)
                if res.success:
                    return res
            except Exception:
                pass
            return other(text)
        return Parser(parse)

def string_parser(expected):
    def parse(text):
        if text.startswith(expected):
            return ParseResult(expected, text[len(expected):])
        raise ParseError(f"Esperado '{expected}', encontrado '{text[:10]}'")
    return Parser(parse)

def regex_parser(pattern):
    import re
    compiled = re.compile(pattern)
    def parse(text):
        match = compiled.match(text)
        if match:
            val = match.group(0)
            return ParseResult(val, text[len(val):])
        raise ParseError(f"Padrão '{pattern}' não correspondeu em '{text[:10]}'")
    return Parser(parse)

def whitespace():
    return regex_parser(r"^[ \t\n\r]*")

def token(p):
    def parse(text):
        ws_res = whitespace()(text)
        res = p(ws_res.rest)
        if not res.success:
            return res
        ws_res2 = whitespace()(res.rest)
        res.rest = ws_res2.rest
        return res
    return Parser(parse)

# Parsers primitivos de JSON
def parse_null():
    return string_parser("null").map(lambda _: None)

def parse_bool():
    true_p = string_parser("true").map(lambda _: True)
    false_p = string_parser("false").map(lambda _: False)
    return true_p.or_else(false_p)

def parse_number():
    return regex_parser(r"^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?").map(
        lambda s: float(s) if '.' in s or 'e' in s.lower() else int(s)
    )

def parse_string():
    def parse(text):
        if not text.startswith('"'):
            raise ParseError("String deve começar com aspas")
        i = 1
        while i < len(text):
            if text[i] == '"' and text[i-1] != '\\':
                val = text[1:i]
                # Tratamento básico de escapes comuns
                val = val.replace('\\"', '"').replace('\\\\', '\\').replace('\\n', '\n')
                return ParseResult(val, text[i+1:])
            i += 1
        raise ParseError("String não terminada")
    return Parser(parse)

# Forward declaration para recursão
def parse_value(text):
    return token(
        parse_null()
        .or_else(parse_bool())
        .or_else(parse_number())
        .or_else(parse_string())
        .or_else(parse_array())
        .or_else(parse_object())
    )(text)

def parse_array():
    def parse(text):
        if not text.startswith('['):
            raise ParseError("Array deve começar com '['")
        rest = text[1:]
        elements = []
        
        ws_res = whitespace()(rest)
        rest = ws_res.rest
        
        if rest.startswith(']'):
            return ParseResult([], rest[1:])
            
        while True:
            val_res = parse_value(rest)
            elements.append(val_res.value)
            rest = val_res.rest
            
            ws_res = whitespace()(rest)
            rest = ws_res.rest
            
            if rest.startswith(']'):
                return ParseResult(elements, rest[1:])
            elif rest.startswith(','):
                rest = rest[1:]
            else:
                raise ParseError(f"Esperado ',' ou ']', encontrado '{rest[:10]}'")
    return Parser(parse)

def parse_object():
    def parse(text):
        if not text.startswith('{'):
            raise ParseError("Objeto deve começar com '{'")
        rest = text[1:]
        obj = {}
        
        ws_res = whitespace()(rest)
        rest = ws_res.rest
        
        if rest.startswith('}'):
            return ParseResult({}, rest[1:])
            
        while True:
            ws_res = whitespace()(rest)
            if not ws_res.rest.startswith('"'):
                raise ParseError("Esperado chave string no objeto")
            
            key_res = parse_string()(ws_res.rest)
            key = key_res.value
            rest = key_res.rest
            
            ws_res = whitespace()(rest)
            if not ws_res.rest.startswith(':'):
                raise ParseError("Esperado ':' após chave do objeto")
            rest = ws_res.rest[1:]
            
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
    return Parser(parse)

def json_parse(text):
    res = token(Parser(parse_value))(text)
    if res.rest:
        raise ParseError(f"Caracteres extras no final do JSON: '{res.rest}'")
    return res.value

if __name__ == "__main__":
    # Demonstração e testes integrados observáveis
    json_valido = '{"nome": "Vanusta", "idade": 42, "ativo": true, "tags": ["ia", "parser"], "filho": null}'
    resultado = json_parse(json_valido)
    print("JSON Válido Parseado com Sucesso:")
    print(resultado)
    assert resultado["nome"] == "Vanusta"
    assert resultado["idade"] == 42
    assert resultado["ativo"] is True
    assert resultado["tags"] == ["ia", "parser"]
    assert resultado["filho"] is None

    # Testando contraexemplo de falha de sintaxe
    json_invalido = '{"nome": "Incompleto"'
    try:
        json_parse(json_invalido)
    except ParseError as e:
        print(f"\nErro capturado corretamente no JSON inválido: {e}")
        assert True