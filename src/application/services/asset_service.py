"""
Asset Service - Use Case: Gestione Lifecycle Asset.
Orchestra la creazione, il recupero, la modifica del rischio e la rimozione
degli asset aziendali tramite Repository e Cache locale.
"""

import logging

from src.application.dto import AssetDTO
from src.application.mappers import AssetMapper
from src.application.services.base_service import BaseService
from src.domain import Asset

logger = logging.getLogger("RGD-Alpha.AssetService")


class AssetService(BaseService):
    """
    Servizio per la gestione degli asset.
    Orchestra le operazioni sugli asset garantendo la sicurezza multi-tenant (company_id).
    """

    def __init__(self, asset_repo=None):
        """Inizializza AssetService con il repository (Dependency Injection)."""
        super().__init__("AssetService")
        self.asset_repo = asset_repo
        self._assets_store: dict[str, Asset] = {}  # Cache/Backup in memoria

    def create_asset(self, asset: Asset) -> AssetDTO:
        """
        Salva o registra un nuovo asset per l'azienda.
        """
        self.log_info(
            f"Salvataggio asset '{asset.nome}' (ID: {asset.id}) per Company: {asset.company_id}"
        )
        try:
            # 1. Persistenza su database (Repository)
            if self.asset_repo:
                self.asset_repo.create(asset)

            # 2. Aggiornamento cache in memoria
            self._assets_store[asset.id] = asset

            return AssetMapper.to_dto(asset)
        except Exception as e:
            self.log_error(
                f"Errore durante il salvataggio dell'asset '{asset.nome}'", e
            )
            raise

    def get_asset(self, asset_id: str, company_id: str) -> AssetDTO | None:
        """
        Recupera un asset specifico verificando la proprietà della company.
        """
        self.log_debug(f"Recupero asset {asset_id} per Company {company_id}")

        asset: Asset | None = None

        # 1. Tentativo di lettura da Repository reale
        if self.asset_repo:
            try:
                asset = self.asset_repo.read(asset_id)
            except Exception as e:
                self.log_warning(
                    f"Impossibile leggere l'asset {asset_id} dal repository: {e}"
                )

        # 2. Fallback alla cache in memoria
        if not asset:
            asset = self._assets_store.get(asset_id)

        # 3. Verifica sicurezza Tenant (company_id)
        if not asset or asset.company_id != company_id:
            return None

        return AssetMapper.to_dto(asset)

    def list_assets(self, company_id: str) -> list[AssetDTO]:
        """
        Elenca tutti gli asset appartenenti a una specifica azienda.
        """
        self.log_info(f"Elenco asset per Company: {company_id}")

        company_assets: list[Asset] = []

        if self.asset_repo:
            try:
                all_assets = self.asset_repo.list_all()
                company_assets = [
                    a
                    for a in all_assets
                    if getattr(a, "company_id", None) == company_id
                ]
            except Exception as e:
                self.log_error("Errore recupero lista asset dal repository", e)
                company_assets = [
                    a for a in self._assets_store.values() if a.company_id == company_id
                ]
        else:
            company_assets = [
                a for a in self._assets_store.values() if a.company_id == company_id
            ]

        # Utilizza il mapper per convertire la lista in DTO
        if hasattr(AssetMapper, "to_dtos"):
            return AssetMapper.to_dtos(company_assets)
        return [AssetMapper.to_dto(a) for a in company_assets]

    def update_asset_risk(
        self, asset_id: str, company_id: str, new_risk_value: float
    ) -> AssetDTO:
        """
        Aggiorna il punteggio di rischio di un asset specifico.
        """
        self.log_info(
            f"Aggiornamento rischio per asset {asset_id} -> Nuovo valore: {new_risk_value}"
        )

        # 1. Recupera l'entità (da DB o cache)
        asset: Asset | None = None
        if self.asset_repo:
            try:
                asset = self.asset_repo.read(asset_id)
            except Exception:
                pass

        if not asset:
            asset = self._assets_store.get(asset_id)

        # 2. Verifica validità e sicurezza Tenant
        if not asset or asset.company_id != company_id:
            raise ValueError(
                f"Asset '{asset_id}' non trovato o non autorizzato per l'azienda {company_id}"
            )

        # 3. Applica modifica del rischio sull'entità di dominio
        if hasattr(asset, "aggiorna_rischio"):
            asset.aggiorna_rischio(new_risk_value)
        elif hasattr(asset, "rischio"):
            asset.rischio = new_risk_value

        # 4. Salva sia sul Repository che nella cache
        if self.asset_repo:
            try:
                self.asset_repo.update(asset_id, asset)
            except Exception as e:
                self.log_error(
                    f"Errore durante l'aggiornamento dell'asset {asset_id} nel DB", e
                )

        self._assets_store[asset_id] = asset

        return AssetMapper.to_dto(asset)

    def get_critical_assets(self, company_id: str) -> list[AssetDTO]:
        """
        Recupera soltanto gli asset contrassegnati come CRITICI per l'azienda.
        """
        self.log_info(f"Recupero asset critici per Company: {company_id}")
        all_assets = self.list_assets(company_id)
        return [a for a in all_assets if getattr(a, "is_critical", False)]

    def delete_asset(self, asset_id: str, company_id: str) -> bool:
        """
        Rimuove un asset sia dal repository che dalla cache locale.
        """
        self.log_info(f"Cancellazione asset {asset_id} per Company {company_id}")

        # Verifica esistenza
        asset_dto = self.get_asset(asset_id, company_id)
        if not asset_dto:
            return False

        # Rimuovi dal repository
        if self.asset_repo:
            try:
                self.asset_repo.delete(asset_id)
            except Exception as e:
                self.log_error(
                    f"Errore durante la cancellazione dell'asset {asset_id} dal repository",
                    e,
                )

        # Rimuovi dalla cache
        self._assets_store.pop(asset_id, None)
        return True
