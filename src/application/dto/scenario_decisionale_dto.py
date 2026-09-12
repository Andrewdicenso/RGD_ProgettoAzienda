from dataclasses import dataclass


@dataclass
class ScenarioDecisionaleDTO:
    asset_id: str
    asset_nome: str
    decisione: str
    variazione_rischio: float
    variazione_kpi: dict
    impatto_finanziario: float
    valutazione_ai: str
