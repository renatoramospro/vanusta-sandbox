import hashlib
import hmac
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

# ==========================================
# 1. SETUP DE SEGURANÇA E NAMESPACES SAML
# ==========================================
CHAVE_SECRETA_IDP = b"chave-privada-simulada-do-idp-2026"

# Registro explícito de namespaces para evitar "unbound prefix" no ElementTree
ET.register_namespace('samlp', 'urn:oasis:names:tc:SAML:2.0:protocol')
ET.register_namespace('saml', 'urn:oasis:names:tc:SAML:2.0:assertion')

def assinar_dados(dados: bytes) -> str:
    return hmac.new(CHAVE_SECRETA_IDP, dados, hashlib.sha256).hexdigest()

def verificar_assinatura(dados: bytes, assinatura_recebida: str) -> bool:
    assinatura_calculada = assinar_dados(dados)
    return hmac.compare_digest(assinatura_calculada, assinatura_recebida)

# ==========================================
# 2. FLUXO SAML: AUTHNREQUEST E RESPONSE
# ==========================================
def criar_authn_request(sp_entity_id, idp_sso_url):
    root = ET.Element("{urn:oasis:names:tc:SAML:2.0:protocol}AuthnRequest", {
        "ID": "_req_123456789",
        "Version": "2.0",
        "IssueInstant": datetime.now(timezone.utc).isoformat(),
        "Destination": idp_sso_url
    })
    issuer = ET.SubElement(root, "{urn:oasis:names:tc:SAML:2.0:assertion}Issuer")
    issuer.text = sp_entity_id
    
    xml_str = ET.tostring(root, encoding="utf-8")
    print(f"[SP] AuthnRequest gerado para {idp_sso_url}")
    return xml_str

def criar_saml_response(idp_entity_id, sp_entity_id, atributos_usuario):
    # Criação do Response com namespaces corretos
    response = ET.Element("{urn:oasis:names:tc:SAML:2.0:protocol}Response", {
        "ID": "_resp_abcdef",
        "Version": "2.0",
        "IssueInstant": datetime.now(timezone.utc).isoformat()
    })
    
    issuer_resp = ET.SubElement(response, "{urn:oasis:names:tc:SAML:2.0:assertion}Issuer")
    issuer_resp.text = idp_entity_id

    # Cria a Assertion
    not_on_or_after = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    assertion = ET.SubElement(response, "{urn:oasis:names:tc:SAML:2.0:assertion}Assertion", {
        "ID": "_assertion_xyz987",
        "Version": "2.0",
        "IssueInstant": datetime.now(timezone.utc).isoformat()
    })
    
    issuer = ET.SubElement(assertion, "{urn:oasis:names:tc:SAML:2.0:assertion}Issuer")
    issuer.text = idp_entity_id
    
    subject = ET.SubElement(assertion, "{urn:oasis:names:tc:SAML:2.0:assertion}Subject")
    name_id = ET.SubElement(subject, "{urn:oasis:names:tc:SAML:2.0:assertion}NameID")
    name_id.text = atributos_usuario.get("email", "usuario@vanusta.edu")

    conditions = ET.SubElement(assertion, "{urn:oasis:names:tc:SAML:2.0:assertion}Conditions", {
        "NotOnOrAfter": not_on_or_after
    })
    
    attr_stmt = ET.SubElement(assertion, "{urn:oasis:names:tc:SAML:2.0:assertion}AttributeStatement")
    for chave, valor in atributos_usuario.items():
        attr = ET.SubElement(attr_stmt, "{urn:oasis:names:tc:SAML:2.0:assertion}Attribute", {"Name": chave})
        attr_val = ET.SubElement(attr, "{urn:oasis:names:tc:SAML:2.0:assertion}AttributeValue")
        attr_val.text = str(valor)

    response_bytes = ET.tostring(response, encoding="utf-8")
    assinatura = assinar_dados(response_bytes)
    
    print(f"[IdP] Resposta SAML gerada e assinada para o usuário: {atributos_usuario.get('email')}")
    return response_bytes, assinatura

def validar_saml_response(response_bytes, assinatura_recebida, sp_esperado):
    # 1. Validação Criptográfica (Integridade)
    if not verificar_assinatura(response_bytes, assinatura_recebida):
        return False, "Falha na verificação da assinatura digital!", {}

    # 2. Parsing XML seguro
    try:
        root = ET.fromstring(response_bytes)
    except Exception as e:
        return False, f"Erro ao processar XML: {e}", {}

    # 3. Validação Temporal (NotOnOrAfter)
    conditions_elem = root.find(".//{urn:oasis:names:tc:SAML:2.0:assertion}Conditions")
    if conditions_elem is not None:
        not_on_or_after_str = conditions_elem.get("NotOnOrAfter")
        if not_on_or_after_str:
            not_on_or_after_dt = datetime.fromisoformat(not_on_or_after_str)
            if datetime.now(timezone.utc) >= not_on_or_after_dt:
                return False, "Assertion expirada (NotOnOrAfter violado)", {}

    # Extração de Atributos
    atributos = {}
    name_id_elem = root.find(".//{urn:oasis:names:tc:SAML:2.0:assertion}NameID")
    if name_id_elem is not None:
        atributos["NameID"] = name_id_elem.text

    for attr in root.findall(".//{urn:oasis:names:tc:SAML:2.0:assertion}Attribute"):
        nome = attr.get("Name")
        val_elem = attr.find("{urn:oasis:names:tc:SAML:2.0:assertion}AttributeValue")
        if val_elem is not None:
            atributos[nome] = val_elem.text

    return True, "Sucesso", atributos

# ==========================================
# 3. EXECUÇÃO DOS TESTES E CONTRAEXEMPLO
# ==========================================
if __name__ == "__main__":
    print("=== INICIANDO SIMULAÇÃO SAML 2.0 (Corrigido) ===")
    
    sp_id = "https://sp.vanusta.edu/saml/metadata"
    idp_id = "https://idp.okta.com/saml2"

    # Passo 1: AuthnRequest
    authn_req = criar_authn_request(sp_id, idp_id)

    # Passo 2: Resposta IdP Legítima
    usuario_valido = {
        "email": "candidato@vanusta.edu",
        "cargo": "Engenheiro",
        "departamento": "TI"
    }
    resp_bytes, sig = criar_saml_response(idp_id, sp_id, usuario_valido)

    # Passo 3: Validação da Resposta Legítima
    valido, msg, attrs = validar_saml_response(resp_bytes, sig, sp_id)
    print(f"[3] Validação de Resposta Legítima: Sucesso={valido} | Atributos={attrs}")
    assert valido, f"Erro: A resposta legítima deveria ser válida! Motivo: {msg}"

    # Passo 4: Contraexemplo de XML Tampering (Adulteração de Atributos)
    print("\n[4] Executando Contraexemplo: Tentativa de XML Tampering...")
    usuario_adulterado = {
        "email": "candidato@vanusta.edu",
        "cargo": "Diretor",  # Tentativa de elevação de privilégio
        "departamento": "TI"
    }
    # Geramos resposta adulterada mas mantemos a assinatura antiga
    resp_adul_bytes, _ = criar_saml_response(idp_id, sp_id, usuario_adulterado)
    
    valido_fake, msg_fake, _ = validar_saml_response(resp_adul_bytes, sig, sp_id)
    print(f"[4] Validação de Resposta Adulterada: {msg_fake}")
    assert not valido_fake, "ERRO DE SEGURANÇA: O sistema aceitou uma resposta com assinatura adulterada!"
    print("-> Contraexemplo bem-sucedido: O sistema rejeitou a adulteração dos atributos.")

    print("\n=== EXPERIMENTO CONCLUÍDO COM SUCESSO (Código 0) ===")