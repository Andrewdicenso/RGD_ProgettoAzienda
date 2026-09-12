from dataclasses import dataclass


@dataclass
class StrategicAnalysisDTO:
    asset_id: str
    asset_nome: str
    rischio: float
    settore: str
    kpi_sintesi: dict
    raccomandazione_operativa: str
    raccomandazione_finanziaria: str
    raccomandazione_magazzino: str
    priorita: str
