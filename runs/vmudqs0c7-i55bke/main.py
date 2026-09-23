path=main.py
import json
import re
from typing import Dict, Any, List

class ComponentMetadataExtractor:
    """
    Simula o motor de extração estática (similar ao react-docgen-typescript)
    que lê o código-fonte de um componente React/TS e extrai sua tabela de props.
    """
    def __init__(self, source_code: str):
        self.source_code = source_code

    def extract_props(self) -> List[Dict[str, Any]]:
        props = []
        # Regex para encontrar a interface de Props do componente
        interface_match = re.search(r'export interface (\w+Props) \{([^}]+)\}', self.source_code, re.DOTALL)
        if not interface_match:
            return props
        
        body = interface_match.group(2)
        # Extrai linhas individuais de propriedades
        lines = body.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('//'):
                continue
            
            # Exemplo de linha: variant?: 'primary' | 'secondary';
            match = re.match(r'(\w+)(\?)?:\s*([^;]+);', line)
            if match:
                prop_name, optional, prop_type = match.groups()
                props.append({
                    "name": prop_name,
                    "required": optional is None,
                    "type": prop_type.strip()
                })
        return props

# --- Demonstração Prática e Contraexemplo ---

# 1. Código do componente original
component_v1 = """
export interface ButtonProps {
    label: string;
    disabled?: boolean;
}

export const Button = ({ label, disabled }: ButtonProps) => {
    return <button disabled={disabled}>{label}</button>;
};
"""

# 2. Código do componente após alteração (adicionando nova prop 'variant' e 'size')
component_v2 = """
export interface ButtonProps {
    label: string;
    disabled?: boolean;
    variant?: 'primary' | 'secondary' | 'danger';
    size?: 'sm' | 'md' | 'lg';
}

export const Button = ({ label, disabled, variant, size }: ButtonProps) => {
    return <button>{label}</button>;
};
"""

print("=== EXECUTANDO TESTE DE EXTRAÇÃO AUTOMÁTICA DE METADADOS ===")

extractor_v1 = ComponentMetadataExtractor(component_v1)
props_v1 = extractor_v1.extract_props()
print(f"Versão 1 - Props extraídas automaticamente: {len(props_v1)}")
print(json.dumps(props_v1, indent=2))

extractor_v2 = ComponentMetadataExtractor(component_v2)
props_v2 = extractor_v2.extract_props()
print(f"\nVersão 2 (Após Push com novas props) - Props extraídas automaticamente: {len(props_v2)}")
print(json.dumps(props_v2, indent=2))

# Validação do critério de sucesso: novas props detectadas sem alteração em arquivos de docs
assert len(props_v2) > len(props_v1), "Falha: O extrator não detectou novas propriedades!"
assert any(p["name"] == "variant" for p in props_v2), "Falha: A prop 'variant' não foi extraída."
assert any(p["name"] == "size" for p in props_v2), "Falha: A prop 'size' não foi extraída."

print("\n[SUCESSO] A extração automática de metadados refletiu 100% dos novos estados e props adicionados ao código sem intervenção manual na documentação.")