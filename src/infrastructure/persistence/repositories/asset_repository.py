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
        print("DEBUG: AssetRepository inizializzato con tabella =", self._table)

    def _to_dict(self, asset: Asset) -> dict[str, Any]:
        """Converte l'oggetto Asset nel formato colonne di Supabase."""
        print("DEBUG: converto asset in dict =", asset)

        rischio_val = (
            asset.rischio.value
            if hasattr(asset.rischio, "value")
            else float(asset.rischio)
        )
        volatilita_val = (
            asset.volatilita.value if hasattr(asset.volatilita, "value") else 0.0
        )

        cat_val = (
            asset.categoria.value
            if hasattr(asset.categoria, "value")
            else str(asset.categoria)
        )

        momentum_status_val = (
            str(asset.momentum.status.value)
            if hasattr(asset, "momentum") and hasattr(asset.momentum, "status")
            else "UNDEFINED"
        )

        momentum_val = (
            float(asset.momentum.value)
            if hasattr(asset, "momentum") and hasattr(asset.momentum, "value")
            else 0.0
        )

        result = {
            "id": asset.id,
            "company_id": asset.company_id,
            "nome": asset.nome,
            "categoria": cat_val,
            "rischio": rischio_val,
            "volatilita": volatilita_val,
            "momentum_status": momentum_status_val,
            "momentum_value": momentum_val,
        }

        print("DEBUG: dict finale per Supabase =", result)
        return result

    def _to_entity(self, data: dict[str, Any]) -> Asset:
        """Ricostruisce l'entità corretta usando la Factory del dominio."""
        print("DEBUG: dati letti da Supabase =", data)

        # 1️⃣ Recupera i campi principali, anche con fallback
        nome = data.get("nome") or data.get("nome_asset") or "Senza Nome"
        rischio = data.get("rischio") or data.get("risk_score") or 0.0
        volatilita = data.get("volatilita") or data.get("volatility") or 0.0

        # 2️⃣ Determina la categoria leggendo correttamente la colonna 'categoria' (con fallback su 'tipo')
        cat_str = data.get("categoria") or data.get("tipo") or "GENERAL"
        cat_str = cat_str.upper()
        try:
            categoria = AssetCategory[cat_str]
        except (KeyError, AttributeError):
            categoria = AssetCategory.GENERAL

        # 3️⃣ Ricostruisci l'entità mappando tutti i campi richiesti
        entity_data = {
            "id": data.get("id"),
            "company_id": data.get("company_id"),
            "nome": nome,
            "rischio": rischio,
            "volatilita": volatilita,
            "tipo": cat_str,
            "momentum_status": data.get("momentum_status"),
            "momentum_value": data.get("momentum_value"),
            "dati_extra": data.get("dati_extra"),
        }

        print("DEBUG: entità ricostruita =", entity_data)

        return crea_asset_dal_dizionario(entity_data, categoria)

    def create(self, asset: Asset) -> Asset:
        """Crea e salva un asset su Supabase."""
        print("DEBUG: entro in create() con asset =", asset)

        data = self._to_dict(asset)
        response = self.db.table(self._table).insert(data).execute()

        print("DEBUG: risposta Supabase create =", response)
        self.log_info(f"Asset creato su Supabase: {asset.nome} ({asset.id})")
        return asset

    def read(self, id: str) -> Asset | None:
        """Legge un asset per ID da Supabase."""
        print("DEBUG: entro in read() con id =", id)

        response = self.db.table(self._table).select("*").eq("id", id).execute()
        print("DEBUG: risposta Supabase read =", response)

        if response.data:
            entity = self._to_entity(response.data[0])
            print("DEBUG: entità letta =", entity)
            return entity

        print("DEBUG: nessun asset trovato con id =", id)
        return None

    def read_by_company(self, company_id: str) -> list[Asset]:
        """Legge tutti gli asset di una company."""
        print("DEBUG: entro in read_by_company() con company_id =", company_id)

        response = (
            self.db.table(self._table)
            .select("*")
            .eq("company_id", company_id)
            .execute()
        )

        print("DEBUG: risposta Supabase read_by_company =", response)

        entities = [self._to_entity(item) for item in response.data]
        print("DEBUG: entità trovate =", entities)
        return entities

    def update(self, asset: Asset) -> Asset:
        """Aggiorna un asset su Supabase."""
        print("DEBUG: entro in update() con asset =", asset)

        data = self._to_dict(asset)
        response = self.db.table(self._table).update(data).eq("id", asset.id).execute()

        print("DEBUG: risposta Supabase update =", response)
        self.log_info(f"Asset aggiornato su Supabase: {asset.id}")
        return asset

    def delete(self, id: str) -> bool:
        """Cancella un asset da Supabase."""
        print("DEBUG: entro in delete() con id =", id)

        response = self.db.table(self._table).delete().eq("id", id).execute()
        print("DEBUG: risposta Supabase delete =", response)

        if response.data:
            self.log_info(f"Asset eliminato: {id}")
            return True

        print("DEBUG: nessun asset eliminato con id =", id)
        return False

    def list_all(self) -> list[Asset]:
        """Lista tutti gli asset registrati."""
        print("DEBUG: entro in list_all()")

        response = self.db.table(self._table).select("*").execute()
        print("DEBUG: risposta Supabase list_all =", response)

        entities = [self._to_entity(item) for item in response.data]
        print("DEBUG: entità trovate =", entities)
        return entities

    def list_critical(self, company_id: str) -> list[Asset]:
        """Ottimizzazione: Filtra gli asset critici direttamente in Supabase."""
        print("DEBUG: entro in list_critical() con company_id =", company_id)

        response = (
            self.db.table(self._table)
            .select("*")
            .eq("company_id", company_id)
            .gt("rischio", 70)
            .execute()
        )

        print("DEBUG: risposta Supabase list_critical =", response)

        entities = [self._to_entity(item) for item in response.data]
        print("DEBUG: asset critici trovati =", entities)
        return entities
