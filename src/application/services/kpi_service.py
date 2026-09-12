class KPIService:
    def __init__(self, kpi_repo):
        self.kpi_repo = kpi_repo

    def calcola_kpi(self, df):
        required = {
            "KPI_Produttività",
            "KPI_Efficienza",
            "KPI_Rendimento",
            "KPI_Saturazione",
        }

        if not required.issubset(df.columns):
            return {
                "success": False,
                "messaggio": "❌ KPI non calcolabili: colonne mancanti.",
                "kpi": {},
            }

        return {
            "success": True,
            "messaggio": "✔️ KPI calcolati correttamente.",
            "kpi": {
                "produttivita": df["KPI_Produttività"].mean(),
                "efficienza": df["KPI_Efficienza"].mean(),
                "rendimento": df["KPI_Rendimento"].mean(),
                "saturazione": df["KPI_Saturazione"].mean(),
            },
        }
