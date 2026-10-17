python path=saml_simulator.py
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
# 2. SERVICE PROVIDER (SP): AuthnRequest
# ==========================================
def criar_authn_request(sp_entity_id, idp_sso_url):
    """Gera um AuthnRequest SAML simplificado (Equívoco 3: HTTP-Redirect/POST)"""
    req_id = "_" + os_random_hex(10)
    issue_instant = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    xml_request = f"""<samlp:AuthnRequest 
        xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol" 
        xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion" 
        ID="{req_id}" 
        Version="2.0" 
        IssueInstant="{issue_instant}" 
        AssertionConsumerServiceURL="https://sp.vanusta.internal/saml/acs"
        ProtocolBinding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST">
        <saml:Issuer>{sp_entity_id}</saml:Issuer>
    </samlp:AuthnRequest>"""
    return xml_request

def os_random_hex(n):
    import secrets
    return secrets.token_hex(n)

# ==========================================
# 3. IDENTITY PROVIDER (IdP): SAML Response & Assinatura
# ==========================================
def criar_saml_response(idp_entity_id, sp_entity_id, user_attributes, private_key):
    """Cria e assina digitalmente uma Resposta SAML (Equívoco 2: Assinatura e XML)"""
    resp_id = "_" + os_random_hex(10)
    assertion_id = "_" + os_random_hex(10)
    issue_instant = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Monta a estrutura XML da Assertion com os atributos do usuário
    attrs_xml = ""
    for k, v in user_attributes.items():
        attrs_xml += f"""
            <saml:Attribute Name="{k}">
                <saml:AttributeValue>{v}</saml:AttributeValue>
            </saml:Attribute>"""

    assertion_xml = f"""<saml:Assertion xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion" ID="{assertion_id}" Version="2.0" IssueInstant="{issue_instant}">
        <saml:Issuer>{idp_entity_id}</saml:Issuer>
        <saml:Subject>
            <saml:NameID Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress">{user_attributes.get('email')}</saml:NameID>
        </saml:Subject>
        <saml:AttributeStatement>{attrs_xml}
        </saml:AttributeStatement>
    </saml:Assertion>"""

    # Assinatura digital simples baseada no hash da assertion (simulando XML Signature)
    digest = hashes.Hash(hashes.SHA256())
    digest.update(assertion_xml.encode('utf-8'))
    signature_bytes = private_key.sign(
        digest.finalize(),
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    signature_b64 = base64.b64encode(signature_bytes).decode('utf-8')

    saml_response = f"""<samlp:Response xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol" ID="{resp_id}" Version="2.0" IssueInstant="{issue_instant}">
        <saml:Issuer xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion">{idp_entity_id}</saml:Issuer>
        {assertion_xml}
        <Signature xmlns="http://www.w3.org/2000/09/xmldsig#">
            <SignatureValue>{signature_b64}</SignatureValue>
        </Signature>
    </samlp:Response>"""
    
    return saml_response, assertion_xml, signature_bytes

# ==========================================
# 4. VALIDAÇÃO PELO SERVICE PROVIDER (SP)
# ==========================================
def validar_saml_response(saml_response_str, assertion_str, signature_bytes, public_key):
    """Valida a assinatura criptográfica e lê os atributos"""
    # Recalcula o hash da assertion recebida
    digest = hashes.Hash(hashes.SHA256())
    digest.update(assertion_str.encode('utf-8'))
    
    try:
        # Verifica a assinatura com a chave pública do IdP
        public_key.verify(
            signature_bytes,
            digest.finalize(),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return True, "Assinatura válida! Autenticação bem-sucedida."
    except Exception as e:
        return False, f"Falha na validação da assinatura: {str(e)}"

# ==========================================
# EXECUÇÃO DO EXPERIMENTO E TESTES PRÁTICOS
# ==========================================
if __name__ == "__main__":
    print("=== INICIANDO EXPERIMENTO: SIMULAÇÃO DE FLUXO SAML 2.0 ===")
    
    # 1. Configurar IdP e SP
    idp_id = "https://idp.okta-simulado.com"
    sp_id = "https://sp.vanusta.internal"
    
    priv_key, cert = gerar_par_chaves_e_certificado()
    pub_key = cert.public_key()
    
    # 2. SP envia requisição
    authn_req = criar_authn_request(sp_id, idp_id)
    print(f"[1] SP gerou AuthnRequest (Tamanho: {len(authn_req)} bytes)")
    
    # 3. IdP autentica e responde com atributos de usuário
    usuario = {
        "email": "carlos.silva@empresa-a.com",
        "nome": "Carlos Silva",
        "grupo": "Engenharia"
    }
    response_xml, assertion_xml, sig_bytes = criar_saml_response(idp_id, sp_id, usuario, priv_key)
    print(f"[2] IdP gerou Resposta SAML com atributos para: {usuario['email']}")
    
    # 4. SP valida a resposta legítima
    valido, msg = validar_saml_response(response_xml, assertion_xml, sig_bytes, pub_key)
    print(f"[3] Validação de Resposta Legítima: {msg}")
    assert valido, "A resposta legítima deveria ser válida!"
    
    # --------------------------------------------------
    # CONTRAEXEMPLO: Ataque de Tampering / Modificação de XML
    # --------------------------------------------------
    print("\n--- TESTANDO CONTRAEXEMPLO: Tentativa de adulteração de atributos ---")
    usuario_adulterado = usuario.copy()
    usuario_adulterado["grupo"] = "Administradores" # Atributo alterado maliciosamente!
    
    # Recriamos a assertion adulterada, mas mantemos a assinatura antiga
    _, assertion_adulterada_xml, _ = criar_saml_response(idp_id, sp_id, usuario_adulterado, priv_key)
    # Forçamos o uso da assinatura antiga (que foi gerada para o grupo 'Engenharia')
    
    valido_fake, msg_fake = validar_saml_response(response_xml, assertion_adulterada_xml, sig_bytes, pub_key)
    print(f"[4] Validação de Resposta Adulterada: {msg_fake}")
    assert not valido_fake, "ERRO DE SEGURANÇA: O sistema aceitou uma resposta com assinatura adulterada!"
    print("-> Contraexemplo bem-sucedido: O sistema rejeitou com sucesso a adulteração criptográfica dos atributos.")
    
    print("\n=== EXPERIMENTO CONCLUÍDO COM SUCESSO (Código 0) ===")