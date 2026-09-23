import json
from typing import Dict, List, Any

class MockNetBoxAPI:
    """Simula o comportamento da API REST do NetBox com integridade relacional."""
    def __init__(self):
        self.db = {
            "sites": [{"id": 1, "name": "Datacenter-SP01"}],
            "device_types": [{"id": 10, "model": "Nexus-9300", "manufacturer": "Cisco"}],
            "devices": [],
            "interfaces": []
        }
    
    def get(self, endpoint: str, params: dict) -> List[dict]:
        table = self.db.get(endpoint, [])
        if "name" in params:
            return [item for item in table if item.get("name") == params["name"]]
        if "model" in params:
            return [item for item in table if item.get("model") == params["model"]]
        if "device_id" in params:
            return [item for item in table if item.get("device_id") == params["device_id"]]
        return table

    def post(self, endpoint: str, data: dict) -> dict:
        table = self.db.get(endpoint)
        new_id = max([item["id"] for item in table], default=0) + 1
        data["id"] = new_id
        table.append(data)
        return data

    def put(self, endpoint: str, item_id: int, data: dict) -> dict:
        table = self.db.get(endpoint)
        for item in table:
            if item["id"] == item_id:
                item.update(data)
                return item
        # Correção aplicada: string delimitada corretamente por aspas
        raise KeyError(f"Registro com ID {item_id} não encontrado para update em {endpoint}")


class NetBoxSyncOrchestrator:
    """Orquestra o pipeline de sincronização (Source of Truth - SoT) com tratamento de dependências."""
    def __init__(self, api: MockNetBoxAPI):
        self.api = api
        self.exception_reports = []

    def sync_device(self, discovery_data: dict) -> None:
        print(f"\n[SYNC] Iniciando sincronização para o dispositivo: {discovery_data['hostname']}")

        # 1. Validação de Dependência: Site
        sites = self.api.get("sites", {"name": discovery_data["site"]})
        if not sites:
            print(f"[WARN] Site '{discovery_data['site']}' não encontrado. Criando automaticamente...")
            site = self.api.post("sites", {"name": discovery_data["site"]})
        else:
            site = sites[0]

        # 2. Validação de Dependência: Device Type (Homologação de Hardware)
        device_types = self.api.get("device_types", {"model": discovery_data["model"]})
        if not device_types:
            # Equívoco comum: Tratamento de exceção para ativos não homologados
            error_msg = f"ATIVO NÃO HOMOLOGADO: Modelo '{discovery_data['model']}' para o device '{discovery_data['hostname']}' não existe no Catálogo NetBox."
            print(f"[ERROR] {error_msg}")
            self.exception_reports.append(error_msg)
            return  # Interrompe o fluxo deste ativo específico sem quebrar o pipeline global
        
        device_type = device_types[0]

        # 3. Upsert de Dispositivo (Idempotência por Chave Natural: hostname)
        existing_devices = self.api.get("devices", {"name": discovery_data["hostname"]})
        if existing_devices:
            device_id = existing_devices[0]["id"]
            print(f"[UPDATE] Dispositivo '{discovery_data['hostname']}' já existe (ID: {device_id}). Atualizando estado...")
            self.api.put("devices", device_id, {
                "site_id": site["id"],
                "device_type_id": device_type["id"],
                "status": "active"
            })
        else:
            print(f"[CREATE] Dispositivo '{discovery_data['hostname']} não encontrado. Criando novo registro...")
            new_dev = self.api.post("devices", {
                "name": discovery_data["hostname"],
                "site_id": site["id"],
                "device_type_id": device_type["id"],
                "status": "active"
            })
            device_id = new_dev["id"]

        # 4. Sincronização de Interfaces (Dependência relacional do Device pai)
        for iface_data in discovery_data.get("interfaces", []):
            existing_ifaces = [
                i for i in self.api.get("interfaces", {"device_id": device_id}) 
                if i["name"] == iface_data["name"]
            ]
            if existing_ifaces:
                iface_id = existing_ifaces[0]["id"]
                self.api.put("interfaces", iface_id, {"speed": iface_data["speed"]})
                print(f"[UPDATE] Interface {iface_data['name']} atualizada.")
            else:
                self.api.post("interfaces", {
                    "device_id": device_id,
                    "name": iface_data["name"],
                    "speed": iface_data["speed"]
                })
                print(f"[CREATE] Interface {iface_data['name']} criada.")


if __name__ == "__main__":
    api_client = MockNetBoxAPI()
    orchestrator = NetBoxSyncOrchestrator(api_client)

    # Cenário 1: Dispositivo homologado e válido (Cisco Nexus-9300)
    switch_payload = {
        "hostname": "sw-core-01",
        "site": "Datacenter-SP01",
        "model": "Nexus-9300",
        "interfaces": [
            {"name": "Ethernet1/1", "speed": 100000},
            {"name": "Ethernet1/2", "speed": 100000},
            {"name": "Management0", "speed": 1000}
        ]
    }

    # Primeira execução (Criação)
    orchestrator.sync_device(switch_payload)
    
    # Segunda execução para testar a Idempotência (Deve atualizar, não duplicar)
    print("\n--- Executando Sincronização Novamente (Teste de Idempotência) ---")
    orchestrator.sync_device(switch_payload)

    # Cenário 2: Dispositivo com hardware não homologado (Equívoco comum tratado)
    unknown_hardware_data = {
        "hostname": "sw-edge-unknown",
        "site": "Datacenter-SP01",
        "model": "Unknown-Whitebox-Model",
        "interfaces": []
    }
    orchestrator.sync_device(unknown_hardware_data)

    print("\n--- Relatório de Exceções Gerado pelo Motor ---")
    for report in orchestrator.exception_reports:
        print(f" -> {report}")

    # Validações observáveis finais
    assert len(api_client.db["devices"]) == 1, "Deveria existir exatamente 1 dispositivo cadastrado (o não homologado foi isolado)"
    assert len(api_client.db["interfaces"]) == 3, "Deveria sincronizar exatamente as 3 interfaces do switch validado"
    assert len(orchestrator.exception_reports) == 1, "Deveria registrar exatamente 1 modelo não homologado na exceção"
    print("\n[VERIFICATION] Todos os testes de comportamento do motor de sincronização passaram com sucesso e sem erros de sintaxe!")