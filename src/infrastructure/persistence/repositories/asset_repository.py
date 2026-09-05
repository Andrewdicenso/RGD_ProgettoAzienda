"""
Asset Repository - Persistence per Asset entities tramite Supabase.
"""

from typing import Any

from src.domain import Asset, crea_asset_dal_dizionario
from src.domain.constants import AssetCategory

from .base_repository import BaseRepository


class AssetRepository(BaseRepository[Asset]):
    """
    Repository per Asset collegato a Supabase (tabella: asset_logs).
    """

    def __init__(self, db):
        """Inizializza AssetRepository con il client Supabase."""
        super().__init__("Asset")
        self.db = db
        self._table = "asset_logs"

    def _to_dict(self, asset: Asset) -> dict[str, Any]:
        """Converte l'oggetto Asset nel formato colonne di Supabase (Italiano)."""
        # Estraiamo i valori dai Value Objects del tuo dominio
        rischio_val = (
            asset.rischio.value
            if hasattr(asset.rischio, "value")
            else float(asset.rischio)
        )
        volatilita_val = (
            asset.volatilita.value if hasattr(asset.volatilita, "value") else 0.0
        )

        # Mappa sugli esatti nomi colonne dello screenshot Supabase
        return {
            "id": asset.id,
            "company_id": asset.company_id,
            "nome": asset.nome,
            "tipo": (
                asset.categoria.value
                if hasattr(asset.categoria, "value")
                else str(asset.categoria)
            ),
            "rischio": rischio_val,
            "momentum": (
                str(asset.momentum.status.value)
                if hasattr(asset.momentum, "status")
                else "UNDEFINED"
            ),
            "volatilita": volatilita_val,
        }

    def _to_entity(self, data: dict[str, Any]) -> Asset:
        """Ricostruisce l'entità corretta usando la Factory del dominio."""
        # Determina la categoria per la factory
        cat_str = data.get("tipo", "GENERAL").upper()
        try:
            categoria = AssetCategory[cat_str]
        except (KeyError, AttributeError):
            categoria = AssetCategory.GENERAL

        # Usa la tua factory 'crea_asset_dal_dizionario' per supportare le sottoclassi
        return crea_asset_dal_dizionario(data, categoria)

    def create(self, asset: Asset) -> Asset:
        """Crea e salva un asset su Supabase."""
        data = self._to_dict(asset)
        self.db.table(self._table).insert(data).execute()
        self.log_info(f"Asset creato su Supabase: {asset.nome} ({asset.id})")
        return asset

    def read(self, id: str) -> Asset | None:
        """Legge un asset per ID da Supabase."""
        response = self.db.table(self._table).select("*").eq("id", id).execute()
        return self._to_entity(response.data[0]) if response.data else None

    def read_by_company(self, company_id: str) -> list[Asset]:
        """Legge tutti gli asset di una company."""
        response = (
            self.db.table(self._table)
            .select("*")
            .eq("company_id", company_id)
            .execute()
        )
        return [self._to_entity(item) for item in response.data]

    def update(self, asset: Asset) -> Asset:
        """Aggiorna un asset su Supabase."""
        data = self._to_dict(asset)
        self.db.table(self._table).update(data).eq("id", asset.id).execute()
        self.log_info(f"Asset aggiornato su Supabase: {asset.id}")
        return asset

    def delete(self, id: str) -> bool:
        """Cancella un asset da Supabase."""
        response = self.db.table(self._table).delete().eq("id", id).execute()
        if response.data:
            self.log_info(f"Asset eliminato: {id}")
            return True
        return False

    def list_all(self) -> list[Asset]:
        """Lista tutti gli asset registrati."""
        response = self.db.table(self._table).select("*").execute()
        return [self._to_entity(item) for item in response.data]

    def list_critical(self, company_id: str) -> list[Asset]:
        """Ottimizzazione: Filtra gli asset critici direttamente in Supabase."""
        # Supponendo che 'critico' sia rischio > 70 come discusso
        response = (
            self.db.table(self._table)
            .select("*")
            .eq("company_id", company_id)
            .gt("rischio", 70)
            .execute()
        )
        return [self._to_entity(item) for item in response.data]
