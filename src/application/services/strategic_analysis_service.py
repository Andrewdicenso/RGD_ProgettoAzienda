from src.application.dto.strategic_analysis_dto import StrategicAnalysisDTO


class StrategicAnalysisService:
    def __init__(self, ai_provider, kpi_repo, asset_repo):
        self.ai = ai_provider
        self.kpi_repo = kpi_repo
        self.asset_repo = asset_repo

    def analizza_asset(
        self,
        asset,
        kpi_sintesi: dict | None = None,
        settore: str | None = None,
    ) -> StrategicAnalysisDTO:
        rischio_val = (
            asset.rischio.value
            if hasattr(asset.rischio, "value")
            else float(asset.rischio)
        )
        asset_nome = getattr(asset, "nome", "Senza Nome")
        asset_id = getattr(asset, "id", "N/D")
        settore = settore or getattr(asset, "settore", "Generico")

        kpi_sintesi = kpi_sintesi or {}

        prompt = f"""
        Sei un Chief Strategy Officer.
        Devi produrre una diagnosi strategica completa per un asset aziendale.

        Asset: {asset_nome} (ID: {asset_id})
        Settore: {settore}
        Rischio: {rischio_val}/10

        KPI sintetici: {kpi_sintesi}

        Genera:
        - Una raccomandazione operativa concreta
        - Una raccomandazione finanziaria
        - Una raccomandazione di magazzino/logistica
        - Una priorità (ALTA / MEDIA / BASSA)
        """

        testo = self.ai.generate_text(prompt=prompt)

        # Qui facciamo un parsing semplice: in futuro puoi strutturarlo meglio
        rac_op = "Raccomandazione operativa non disponibile"
        rac_fin = "Raccomandazione finanziaria non disponibile"
        rac_mag = "Raccomandazione magazzino non disponibile"
        priorita = "MEDIA"

        for line in testo.splitlines():
            l = line.strip()
            if l.lower().startswith("operativa"):
                rac_op = l
            elif l.lower().startswith("finanziaria"):
                rac_fin = l
            elif l.lower().startswith("magazzino") or l.lower().startswith("logistica"):
                rac_mag = l
            elif "priorità" in l.lower():
                priorita = l.split(":")[-1].strip().upper()

        return StrategicAnalysisDTO(
            asset_id=asset_id,
            asset_nome=asset_nome,
            rischio=rischio_val,
            settore=settore,
            kpi_sintesi=kpi_sintesi,
            raccomandazione_operativa=rac_op,
            raccomandazione_finanziaria=rac_fin,
            raccomandazione_magazzino=rac_mag,
            priorita=priorita,
        )

    def analisi_portafoglio(
        self, assets: list, kpi_globali: dict | None = None
    ) -> list[StrategicAnalysisDTO]:
        risultati: list[StrategicAnalysisDTO] = []
        for asset in assets:
            dto = self.analizza_asset(asset, kpi_sintesi=kpi_globali or {})
            risultati.append(dto)
        return risultati
