import json
import re
from typing import Dict, Any, List

class TypeScriptDocExtractor:
    """
    Simula o comportamento do react-docgen-typescript, analisando o código-fonte
    de um componente React/TypeScript para extrair metadados (props, tipos, JSDoc)
    de forma puramente estática.
    """
    def __init__(self, source_code: str):
        self.source_code = source_code

    def extract_props(self) -> List[Dict[str, Any]]:
        props = []
        # Expressão regular para capturar propriedades dentro de interfaces TypeScript
        # Ex: /** Descrição */ propName?: type;
        pattern = r'(?:/\*\*\s*(.*?)\s*\*/\s*)?(\w+)(\?)?:\s*([^;]+);'
        matches = re.findall(pattern, self.source_code, re.DOTALL)

        for match in matches:
            doc_comment, prop_name, optional, prop_type = match
            props.append({
                "name": prop_name.strip(),
                "type": prop_type.strip(),
                "required": optional == '',
                "description": doc_comment.strip() if doc_comment else "Sem descrição"
            })
        return props

# Componente V1: Estado inicial com apenas uma propriedade básica
component_v1 = """
export interface ButtonProps {
  /** Texto exibido dentro do botão */
  label: string;
}

export const Button = ({ label }: ButtonProps) => {
  return <button>{label}</button>;
};
"""

# Componente V2: Evolução com novas props e variantes adicionadas ao código
component_v2 = """
export interface ButtonProps {
  /** Texto exibido dentro do botão */
  label: string;
  /** Define a variante visual do botão */
  variant?: 'primary' | 'secondary' | 'danger';
  /** Define o tamanho do botão */
  size?: 'sm' | 'md' | 'lg';
}

export const Button = ({ label, variant = 'primary', size = 'md' }: ButtonProps) => {
  return <button className={`btn-${variant} btn-${size}`}>{label}</button>;
};
"""

print("=== Executando Extração Estática de Metadados (V1) ===")
extractor_v1 = TypeScriptDocExtractor(component_v1)
props_v1 = extractor_v1.extract_props()
print(f"Total de props extraídas automaticamente: {len(props_v1)}")
print(json.dumps(props_v1, indent=2))

print("\n=== Executando Extração Estática de Metadados após alteração no código (V2) ===")
extractor_v2 = TypeScriptDocExtractor(component_v2)
props_v2 = extractor_v2.extract_props()
print(f"Total de props extraídas automaticamente: {len(props_v2)}")
print(json.dumps(props_v2, indent=2))

# Validação estrita do critério de sucesso: novas props detectadas sem alteração em arquivos de docs
assert len(props_v2) > len(props_v1), "Falha: O extrator não detectou novas propriedades!"
assert any(p["name"] == "variant" for p in props_v2), "Falha: A prop 'variant' não foi extraída."
assert any(p["name"] == "size" for p in props_v2), "Falha: A prop 'size' não foi extraída."

print("\n[SUCESSO] A extração automática de metadados refletiu 100% dos novos estados e props adicionados ao código sem intervenção manual na documentação.")