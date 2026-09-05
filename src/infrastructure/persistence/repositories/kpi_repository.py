"""
KPI Repository - Gestione dello storico rischi su Supabase.
Fornisce i dati per l'analisi predittiva del motore RGD-Alpha.
"""

from postgrest.exceptions import APIError

from src.infrastructure.persistence.db.connection import DatabaseConnection
from src.infrastructure.persistence.repositories.base_repository import BaseRepository


class KPIRepository(BaseRepository):
    """Repository per la gestione della cronologia KPI e calcoli di trend."""

    def __init__(self, db: DatabaseConnection):
        """Inizializza la classe base con il nome della tabella kpi_history."""
        super().__init__("kpi_history")
        self.supabase = db.get_client()

    def find_history_for_asset(self, asset_id: str, limit: int = 12) -> list[float]:
        """
        Recupera gli ultimi N punteggi di rischio per un asset.
        Necessario per la regressione lineare dell'AnalysisService.
        """
        try:
            response = (
                self.supabase.table("kpi_history")
                .select("rischio")
                .eq("asset_id", asset_id)
                .order("data", desc=True)
                .limit(limit)
                .execute()
            )
            return [float(row["rischio"]) for row in reversed(response.data)]
        except (APIError, KeyError, ValueError):
            return []

    def record_kpi(self, asset_id: str, user_id: str, rischio: float) -> bool:
        """Registra un nuovo punto nello storico dei rischi."""
        data = {"asset_id": asset_id, "user_id": user_id, "rischio": rischio}
        try:
            response = self.supabase.table("kpi_history").insert(data).execute()
            return len(response.data) > 0
        except (APIError, KeyError, ValueError):
            return False

    # === IMPLEMENTAZIONE METODI OBBLIGATORI (BaseRepository) ===

    def create(self, entity: dict):
        """Implementazione obbligatoria per BaseRepository."""
        return self.supabase.table("kpi_history").insert(entity).execute()

    def read(self, id: str):  # pylint: disable=redefined-builtin
        """Implementazione obbligatoria per BaseRepository."""
        return self.supabase.table("kpi_history").select("*").eq("id", id).execute()

    def update(self, entity: dict):
        """Implementazione obbligatoria per BaseRepository."""
        entity_id = entity.get("id")
        return (
            self.supabase.table("kpi_history")
            .update(entity)
            .eq("id", entity_id)
            .execute()
        )

    def delete(self, id: str):  # pylint: disable=redefined-builtin
        """Implementazione obbligatoria per BaseRepository."""
        return self.supabase.table("kpi_history").delete().eq("id", id).execute()

    def list_all(self):
        """Implementazione obbligatoria per BaseRepository."""
        return self.supabase.table("kpi_history").select("*").execute()
