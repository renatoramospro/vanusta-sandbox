import base64
import zlib
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography import x509
from cryptography.x509.oid import NameOID

# ==========================================
# 1. SETUP DE CERTIFICADOS X.509 (IdP simulado)
# ==========================================
def gerar_par_chaves_e_certificado():
    # Gera chave privada RSA
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    # Cria certificado autoassinado para o IdP
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "BR"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Vanusta Edu"),
        x509.NameAttribute(NameOID.COMMON_NAME, "idp.vanusta.internal"),
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.now(timezone.utc)
    ).not_valid_after(
        datetime.now(timezone.utc).replace(year=datetime.now(timezone.utc).year + 1)
    ).sign(private_key, hashes.SHA256())
    
    return private_key, cert

# ==========================================
# 2. FLUXO SAML: AUTHNREQUEST E RESPONSE
# ==========================================
def criar_authn_request(sp_entity_id, idp_sso_url):
    # Simula a criação de um AuthnRequest em XML
    root = ET.Element("samlp:AuthnRequest", {
        "ID": "_req_123456789",
        "Version": "2.0",
        "IssueInstant": datetime.now(timezone.utc).isoformat(),
        "Destination": idp_sso_url
    })
    issuer = ET.SubElement(root, "saml:Issuer")
    issuer.text = sp_entity_id
    
    xml_str = ET.tostring(root, encoding="utf-8")
    # Bindings HTTP-Redirect frequentemente comprimem e codificam em base64
    deflated = zlib.compress(xml_str)[2:-4] # Remove cabeçalho/trailer zlib padrão do python para compatibilidade deflated
    encoded = base64.b64encode(deflated).decode("utf-8")
    return encoded

def criar_saml_response(idp_entity_id, sp_entity_id, atributos_usuario, private_key):
    # Simula a criação da Resposta SAML com Assertion e Atributos
    response_id = "_resp_abc123"
    assertion_id = "_assert_xyz789"
    issue_instant = datetime.now(timezone.utc).isoformat()
    
    root = ET.Element("samlp:Response", {
        "ID": response_id,
        "Version": "2.0",
        "IssueInstant": issue_instant,
    })
    
    issuer = ET.SubElement(root, "saml:Issuer")
    issuer.text = idp_entity_id
    
    assertion = ET.SubElement(root, "saml:Assertion", {
        "ID": assertion_id,
        "Version": "2.0",
        "IssueInstant": issue_instant,
    })
    
    assert_issuer = ET.SubElement(assertion, "saml:Issuer")
    assert_issuer.text = idp_entity_id
    
    subject = ET.SubElement(assertion, "saml:Subject")
    name_id = ET.SubElement(subject, "saml:NameID", {"Format": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"})
    name_id.text = atributos_usuario["email"]
    
    attr_stmt = ET.SubElement(assertion, "saml:AttributeStatement")
    for k, v in atributos_usuario.items():
        attr = ET.SubElement(attr_stmt, "saml:Attribute", {"Name": k})
        attr_val = ET.SubElement(attr, "saml:AttributeValue")
        attr_val.text = str(v)
        
    assertion_xml = ET.tostring(assertion, encoding="utf-8")
    
    # Assinatura Digital RSA-SHA256 da Assertion
    signature_bytes = private_key.sign(
        assertion_xml,
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    
    return root, assertion_xml, signature_bytes

def validar_saml_response(response_xml_root, assertion_xml, signature_bytes, public_key):
    # 1. Validação da Assinatura Digital (Garante integridade e autenticidade do IdP)
    try:
        public_key.verify(
            signature_bytes,
            assertion_xml,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
    except Exception as e:
        return False, f"Falha na validação da assinatura criptográfica: {str(e)}"
    
    # 2. Parse e extração de atributos se a assinatura for válida
    assertion_root = ET.fromstring(assertion_xml)
    atributos = {}
    for attr in assertion_root.findall(".//{*}Attribute"):
        name = attr.get("Name")
        val = attr.find("{*}AttributeValue").text
        atributos[name] = val
        
    return True, atributos

# ==========================================
# 3. EXECUÇÃO DO EXPERIMENTO E CONTRAEXEMPLO
# ==========================================
if __name__ == "__main__":
    print("=== INICIALIZANDO SIMULADOR SAML 2.0 (VANUSTA) ===")
    
    # Setup de chaves
    priv_key, cert = gerar_par_chaves_e_certificado()
    pub_key = cert.public_key()
    
    sp_id = "https://sp.vanusta.internal/metadata"
    idp_id = "https://idp.okta.com/ex123456"
    
    # Passo 1: AuthnRequest do SP
    authn_req_encoded = criar_authn_request(sp_id, "https://idp.okta.com/sso/saml")
    print(f"[1] AuthnRequest gerado e codificado com sucesso (Tamanho: {len(authn_req_encoded)} chars)")
    
    # Passo 2: IdP autentica o usuário e gera resposta assinada
    usuario_legitimo = {
        "email": "candidato@vanusta.edu",
        "nome": "João Programador",
        "grupo": "Engenharia"
    }
    response_xml, assertion_xml, sig_bytes = criar_saml_response(idp_id, sp_id, usuario_legitimo, priv_key)
    print(f"[2] IdP gerou Resposta SAML e assinou digitalmente a Assertion para: {usuario_legitimo['email']}")
    
    # Passo 3: Validação bem-sucedida pelo SP
    valido, resultado = validar_saml_response(response_xml, assertion_xml, sig_bytes, pub_key)
    print(f"[3] Validação de Resposta Legítima: Sucesso={valido} | Atributos extraídos: {resultado}")
    assert valido, "A validação da resposta legítima falhou!"
    
    # Passo 4: CONTRAEXEMPLO DE SEGURANÇA (XML Tampering / Modificação maliciosa de atributos)
    print("\n--- TESTANDO CONTRAEXEMPLO DE SEGURANÇA (XML Tampering) ---")
    usuario_adulterado = {
        "email": "candidato@vanusta.edu",
        "nome": "João Programador",
        "grupo": "Administradores"  # Atributo injetado maliciosamente por um atacante na rede
    }
    
    # Criamos novos dados mas tentamos passar a assinatura antiga
    _, assertion_adulterada_xml, _ = criar_saml_response(idp_id, sp_id, usuario_adulterado, priv_key)
    # Forçamos o uso da assinatura antiga (que foi gerada para o grupo 'Engenharia')
    
    valido_fake, msg_fake = validar_saml_response(response_xml, assertion_adulterada_xml, sig_bytes, pub_key)
    print(f"[4] Validação de Resposta Adulterada: {msg_fake}")
    assert not valido_fake, "ERRO DE SEGURANÇA: O sistema aceitou uma resposta com assinatura adulterada!"
    print("-> Contraexemplo bem-sucedido: O sistema rejeitou com sucesso a adulteração criptográfica dos atributos.")
    
    print("\n=== EXPERIMENTO CONCLUÍDO COM SUCESSO (Código 0) ===")