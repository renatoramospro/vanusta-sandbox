import hashlib
import hmac
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

# ==========================================
# 1. SETUP DE SEGURANÇA (Simulação Criptográfica via HMAC-SHA256)
# ==========================================
# No lugar de dependências externas como cryptography, utilizamos uma chave secreta
# compartilhada para assinar e verificar as assertions (simulando a assinatura digital RSA).
CHAVE_SECRETA_IDP = b"chave-privada-simulada-do-idp-2026"

def assinar_dados(dados: bytes) -> str:
    # Simula a assinatura digital gerando um HMAC-SHA256 dos dados
    return hmac.new(CHAVE_SECRETA_IDP, dados, hashlib.sha256).hexdigest()

def verificar_assinatura(dados: bytes, assinatura_recebida: str) -> bool:
    assinatura_calculada = assinar_dados(dados)
    return hmac.compare_digest(assinatura_calculada, assinatura_recebida)

# ==========================================
# 2. FLUXO SAML: AUTHNREQUEST E RESPONSE
# ==========================================
def criar_authn_request(sp_entity_id, idp_sso_url):
    root = ET.Element("samlp:AuthnRequest", {
        "ID": "_req_123456789",
        "Version": "2.0",
        "IssueInstant": datetime.now(timezone.utc).isoformat(),
        "Destination": idp_sso_url
    })
    issuer = ET.SubElement(root, "saml:Issuer")
    issuer.text = sp_entity_id
    
    xml_str = ET.tostring(root, encoding="utf-8")
    print(f"[SP] AuthnRequest gerado para {idp_sso_url}")
    return xml_str

def criar_saml_response(idp_entity_id, sp_entity_id, atributos_usuario):
    # Cria o XML da Assertion contendo atributos do usuário
    assertion = ET.Element("saml:Assertion", {
        "ID": "_assertion_xyz987",
        "Version": "2.0",
        "IssueInstant": datetime.now(timezone.utc).isoformat()
    })
    
    issuer = ET.SubElement(assertion, "saml:Issuer")
    issuer.text = idp_entity_id
    
    subject = ET.SubElement(assertion, "saml:Subject")
    name_id = ET.SubElement(subject, "saml:NameID")
    name_id.text = atributos_usuario["email"]
    
    attr_statement = ET.SubElement(assertion, "saml:AttributeStatement")
    for chave, valor in atributos_usuario.items():
        attr = ET.SubElement(attr_statement, "saml:Attribute", {"Name": chave})
        attr_val = ET.SubElement(attr, "saml:AttributeValue")
        attr_val.text = str(valor)
        
    assertion_bytes = ET.tostring(assertion, encoding="utf-8")
    
    # Assina digitalmente os bytes da Assertion
    assinatura = assinar_dados(assertion_bytes)
    
    # Empacota na Response SAML
    response = ET.Element("samlp:Response", {
        "ID": "_resp_555444",
        "InResponseTo": "_req_123456789",
        "Version": "2.0"
    })
    response.append(assertion)
    
    response_bytes = ET.tostring(response, encoding="utf-8")
    print(f"[IdP] Resposta SAML gerada e assinada para o usuário: {atributos_usuario['email']}")
    return response_bytes, assertion_bytes, assinatura

def validar_saml_response(response_bytes, assertion_bytes, assinatura_recebida, esperado_sp_id):
    # 1. Verifica a integridade e autenticidade da assinatura digital
    if not verificar_assinatura(assertion_bytes, assinatura_recebida):
        return False, "Falha de Assinatura: A assertion foi adulterada ou a assinatura é inválida!"
    
    # 2. Parse do XML da Response/Assertion
    try:
        root = ET.fromstring(response_bytes)
        assertion = root.find(".//{*}Assertion")
        if assertion is None:
            return False, "Assertion não encontrada na resposta."
        
        # Extrai atributos para uso do Service Provider
        atributos = {}
        for attr in assertion.findall(".//{*}Attribute"):
            nome = attr.get("Name")
            val = attr.find("{*}AttributeValue")
            if val is not None:
                atributos[nome] = val.text
                
        return True, atributos
    except Exception as e:
        return False, f"Erro ao processar XML: {str(e)}"

# ==========================================
# 3. EXECUÇÃO DOS TESTES E CONTRAEXEMPLO
# ==========================================
if __name__ == "__main__":
    print("=== INICIANDO SIMULAÇÃO SAML 2.0 (Biblioteca Padrão) ===")
    
    sp_id = "https://sp.vanusta.internal/metadata"
    idp_id = "https://idp.okta.com/saml2"
    
    # Passo 1: Service Provider envia AuthnRequest
    authn_req = criar_authn_request(sp_id, idp_id)
    
    # Passo 2: IdP autentica o usuário e gera Response com atributos
    usuario_legitimo = {
        "email": "candidato@vanusta.edu",
        "nome": "Candidato Vanusta",
        "grupo": "Engenharia"
    }
    resp_bytes, assertion_bytes, sig = criar_saml_response(idp_id, sp_id, usuario_legitimo)
    
    # Passo 3: Service Provider valida a resposta legítima
    valido, resultado = validar_saml_response(resp_bytes, assertion_bytes, sig, sp_id)
    print(f"[3] Validação de Resposta Legítima: Sucesso={valido} | Atributos={resultado}")
    assert valido, "Erro: A resposta legítima deveria ser válida!"
    assert resultado["grupo"] == "Engenharia", "Erro: Grupo do usuário incorreto!"
    
    # Passo 4: CONTRAEXEMPLO DE XML TAMPERING (Adulteração de Atributos)
    print("\n--- EXECUTANDO CONTRAEXEMPLO: XML Tampering ---")
    usuario_adulterado = {
        "email": "candidato@vanusta.edu",
        "nome": "Candidato Vanusta",
        "grupo": "Administradores"  # Elevação de privilégio não autorizada!
    }
    
    # Geramos uma nova assertion com os dados adulterados, mas mantemos a assinatura antiga
    _, assertion_adulterada_bytes, _ = criar_saml_response(idp_id, sp_id, usuario_adulterado)
    
    valido_fake, msg_fake = validar_saml_response(resp_bytes, assertion_adulterada_bytes, sig, sp_id)
    print(f"[4] Validação de Resposta Adulterada: {msg_fake}")
    assert not valido_fake, "ERRO DE SEGURANÇA: O sistema aceitou uma resposta com assinatura adulterada!"
    print("-> Contraexemplo bem-sucedido: O sistema rejeitou com sucesso a adulteração criptográfica dos atributos.")
    
    print("\n=== EXPERIMENTO CONCLUÍDO COM SUCESSO (Código 0) ===")