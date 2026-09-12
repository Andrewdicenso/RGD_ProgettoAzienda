from dataclasses import dataclass


@dataclass
class FileCapabilityReportDTO:
    kpi_disponibili: bool
    magazzino_disponibile: bool
    asset_disponibili: bool
    messaggi: list[str]
