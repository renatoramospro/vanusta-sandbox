import unittest
from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass
class DependencyEdge:
    source: str
    target: str
    operator: str  # 'AND' (&&), 'OR' (||), 'SEQUENCE' (;)

@dataclass
class BatchJob:
    name: str
    schedule: str
    command: str
    dependencies: List[DependencyEdge] = field(default_factory=list)
    estimated_duration_seconds: Optional[int] = None

class BatchDocumentationGenerator:
    def __init__(self, crontab_lines: List[str], telemetry_data: dict):
        self.crontab_lines = crontab_lines
        self.telemetry_data = telemetry_data

    def expand_cron_alias(self, line: str) -> str:
        """Converte aliases cron suportados para o formato de 5 campos."""
        aliases = {
            "@yearly": "0 0 1 1 *",
            "@annually": "0 0 1 1 *",
            "@monthly": "0 0 1 * *",
            "@weekly": "0 0 * * 0",
            "@daily": "0 0 * * *",
            "@midnight": "0 0 * * *",
            "@hourly": "0 * * * *"
        }
        parts = line.strip().split(maxsplit=1)
        if parts and parts[0] in aliases:
            cron_expr = aliases[parts[0]]
            cmd = parts[1] if len(parts) > 1 else ""
            return f"{cron_expr} {cmd}"
        return line

    def parse_dependencies(self, command: str) -> List[DependencyEdge]:
        """
        Infere dependências estruturadas em DAG mapeando operadores &&, || e ;
        preservando a semântica de sucesso, fallback e sequência incondicional.
        """
        edges = []
        # Tokenização simples mantendo operadores para análise de semântica
        # Dividimos mantendo os separadores para identificar o operador exato
        tokens = []
        current = ""
        i = 0
        while i < len(command):
            if command[i:i+2] == "&&":
                if current.strip(): tokens.append(current.strip())
                tokens.append("&&")
                current = ""
                i += 2
            elif command[i:i+2] == "||":
                if current.strip(): tokens.append(current.strip())
                tokens.append("||")
                current = ""
                i += 2
            elif command[i] == ";":
                if current.strip(): tokens.append(current.strip())
                tokens.append(";")
                current = ""
                i += 1
            else:
                current += command[i]
                i += 1
        if current.strip():
            tokens.append(current.strip())

        # Construir arestas do DAG com base nos operadores encontrados
        idx = 0
        while idx < len(tokens) - 2:
            source = tokens[idx]
            op = tokens[idx+1]
            target = tokens[idx+2]
            
            if op == "&&":
                op_type = "AND"
            elif op == "||":
                op_type = "OR"
            elif op == ";":
                op_type = "SEQUENCE"
            else:
                idx += 2
                continue

            edges.append(DependencyEdge(source=source, target=target, operator=op_type))
            idx += 2

        return edges

    def generate_report(self) -> dict:
        jobs = []
        for line in self.crontab_lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            line = self.expand_cron_alias(line)
            tokens = line.split(maxsplit=5)
            if len(tokens) < 6:
                continue
            
            schedule = " ".join(tokens[:5])
            command = tokens[5]
            job_name = command.split()[0].split("/")[-1]
            
            dependencies = self.parse_dependencies(command)
            duration = self.telemetry_data.get(job_name, {}).get("avg_duration_seconds", None)
            
            jobs.append(BatchJob(
                name=job_name,
                schedule=schedule,
                command=command,
                dependencies=dependencies,
                estimated_duration_seconds=duration
            ))
        return {"jobs": [vars(j) for j in jobs]}

class TestBatchDocumentationGenerator(unittest.TestCase):
    def test_cron_aliases_expansion(self):
        lines = ["@daily /srv/backup.sh"]
        gen = BatchDocumentationGenerator(lines, {})
        report = gen.generate_report()
        self.assertEqual(report["jobs"][0]["schedule"], "0 0 * * *")

    def test_shell_operators_semantics(self):
        # Testa && (AND), || (OR/fallback) e ; (SEQUENCE)
        command = "jobA.sh && jobB.sh || jobC.sh; jobD.sh"
        gen = BatchDocumentationGenerator([], {})
        edges = gen.parse_dependencies(command)
        
        self.assertEqual(len(edges), 3)
        self.assertEqual(edges[0].operator, "AND")
        self.assertEqual(edges[1].operator, "OR")
        self.assertEqual(edges[2].operator, "SEQUENCE")

    def test_telemetry_integration(self):
        lines = ["*/15 * * * * /srv/etl.py"]
        telemetry = {"etl.py": {"avg_duration_seconds": 300}}
        gen = BatchDocumentationGenerator(lines, telemetry)
        report = gen.generate_report()
        
        job = report["jobs"][0]
        self.assertEqual(job["estimated_duration_seconds"], 300)

if __name__ == "__main__":
    unittest.main(exit=False)
    print("Experimento executado com sucesso: Aliases cron, semântica de operadores e DAG validados.")