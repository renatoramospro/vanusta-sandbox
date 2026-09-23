path=netbox_sync_engine.py
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
        if endpoint == "devices":
            # Validação relacional estrita (simula FK constraint do NetBox)
            site_exists = any(s["id"] == data.get("site_id") for s in self.db["sites"])
            type_exists = any(dt["id"] == data.get("device_type_id") for dt in self.db["device_types"])
            if not site_exists or not type_exists:
                raise ValueError(f"Erro de integridade referencial: Site ou Device Type inválido para {data['name']}")
            
            new_id = len(table) + 1
            record = {**data, "id": new_id}
            table.append(record)
            return record
        
        elif endpoint == "interfaces":
            new_id = len(table) + 1
            record = {**data, "id": new_id}
            table.append(record)
            return record
            
        return {}

    def put(self, endpoint: str, record_id: int, data: dict) -> dict:
        table = self.db.get(endpoint, [])
        for item in table:
            if item["id"] == record_id:
                item.update(data)
                return item
        raise KeyError(Registro não encontrado para update)


class NetworkTopologyDiscovery:
    """Simula a coleta de dados de rede por protocolos de gerência (LLDP/SNMP)."""
    @staticmethod
    def collect_edge_switch() -> Dict[str, Any]:
        return {
            "hostname": "core-sw-01",
            "site": "Datacenter-SP01",
            "model": "Nexus-9300",
            "interfaces": [
                {"name": "Ethernet1/1", "status": "active", "speed_mbps": 10000},
                {"name": "Ethernet1/2", "status": "active", "speed_mbps": 10000},
                {"name": "Ethernet1/3", "status": "down", "speed_mbps": 1000}
            ]
        }


class NetBoxSyncOrchestrator:
    def __init__(self, api: MockNetBoxAPI):
        self.api = api
        self.exception_reports: List[str] = []

    def sync_device(self, discovered_data: dict):
        # 1. Resolução de Dependências: Site
        sites = self.api.get("sites", {"name": discovered_data["site"]})
        if not sites:
            self.exception_reports.append(f"Ativo órfão/rejeitado: Site '{discovered_data['site']}' não cadastrado.")
            return
        site_id = sites[0]["id"]

        # 2. Resolução de Dependências: Device Type (Tratamento do equívoco de hardware não homologado)
        device_types = self.api.get("device_types", {"model": discovered_data["model"]})
        if not device_types:
            self.exception_reports.append(f"Modelo não homologado: '{discovered_data['model']}' para o dispositivo {discovered_data['hostname']}.")
            return
        device_type_id = device_types[0]["id"]

        # 3. Upsert Idempotente de Device
        devices = self.api.get("devices", {"name": discovered_data["hostname"]})
        if devices:
            dev_id = devices[0]["id"]
            print(f"[SYNC] Device '{discovered_data['hostname']}' já existe (ID: {dev_id}). Verificando atualizações...")
            # Atualiza se houver divergência (exemplo simplificado)
        else:
            print(f"[SYNC] Criando novo Device '{discovered_data['hostname']}'...")
            new_dev = self.api.post("devices", {
                "name": discovered_data["hostname"],
                "site_id": site_id,
                "device_type_id": device_type_id
            })
            dev_id = new_dev["id"]

        # 4. Sincronização de Interfaces (Filho do Device)
        for intf in discovered_data["interfaces"]:
            existing_intfs = self.api.get("interfaces", {"device_id": dev_id, "name": intf["name"]})
            # Como a busca simples do mock retorna todas do device, filtramos pelo nome exato:
            exact_match = [i for i in existing_intfs if i["name"] == intf["name"]]
            
            if exact_match:
                # Atualiza estado se mudou
                self.api.put("interfaces", exact_match[0]["id"], {"status": intf["status"]})
            else:
                self.api.post("interfaces", {
                    "device_id": dev_id,
                    "name": intf["name"],
                    "status": intf["status"],
                    "speed_mbps": intf["speed_mbps"]
                })
        print(f"[SUCCESS] Sincronização concluída para {discovered_data['hostname']}.")


if __name__ == "__main__":
    api_client = MockNetBoxAPI()
    orchestrator = NetBoxSyncOrchestrator(api_client)

    # Cenário 1: Coleta normal de um switch homologado
    print("--- EXECUTANDO CICLO 1: Ativo Válido ---")
    topology_data = NetworkTopologyDiscovery.collect_edge_switch()
    orchestrator.sync_device(topology_data)

    # Cenário 2: Tratamento de Exceção (Ativo com modelo não homologado - Equívoco Comum)
    print("\n--- EXECUTANDO CICLO 2: Ativo com Hardware Não Homologado ---")
    unknown_hardware_data = {
        "hostname": "legacy-sw-99",
        "site": "Datacenter-SP01",
        "model": "Obsolete-Switch-X", # Não existe no NetBox
        "interfaces": []
    }
    orchestrator.sync_device(unknown_hardware_data)

    print("\nRelatório de Exceções Gerado pelo Motor:")
    for report in orchestrator.exception_reports:
        print(f" -> {report}")

    # Validações observáveis finais
    assert len(api_client.db["devices"]) == 1, "Deveria existir exatamente 1 dispositivo cadastrado"
    assert len(api_client.db["interfaces"]) == 3, "Deveria sincronizar as 3 interfaces do switch"
    assert len(orchestrator.exception_reports) == 1, "Deveria registrar o modelo não homologado na exceção"
    print("\n[VERIFICATION] Todos os testes de comportamento do motor de sincronização passaram com sucesso!")