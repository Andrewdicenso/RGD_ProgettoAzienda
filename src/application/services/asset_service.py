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
from src.domain.exceptions import InvalidRiscoScoreException
from src.domain.value_objects import RiscoScore

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
        print("DEBUG: entro in create_asset")
        print("DEBUG: asset ricevuto =", asset)

        # Validazione e normalizzazione robusta del rischio tramite RiscoScore Value Object prima della persistenza
        if hasattr(asset, "rischio") and asset.rischio is not None:
            try:
                # Se è già un RiscoScore, manteniamolo o estraiamone il valore correttamente
                if isinstance(asset.rischio, RiscoScore):
                    pass  # Mantiene l'oggetto corretto
                else:
                    val_rischio_float = float(asset.rischio)
                    asset.rischio = RiscoScore(val_rischio_float)
            except (InvalidRiscoScoreException, ValueError, TypeError):
                try:
                    numeric_fallback = (
                        float(asset.rischio.value)
                        if hasattr(asset.rischio, "value")
                        else (
                            float(asset.rischio) if asset.rischio is not None else 0.0
                        )
                    )
                    clamped_val = max(0.0, min(10.0, numeric_fallback))
                    asset.rischio = RiscoScore(clamped_val)
                except Exception:
                    asset.rischio = RiscoScore(0.0)

        self.log_info(
            f"Salvataggio asset '{asset.nome}' (ID: {asset.id}) per Company: {asset.company_id}"
        )
        try:
            # 1. Persistenza su database (Repository)
            if self.asset_repo:
                self.asset_repo.create(asset)

            # 2. Aggiornamento cache in memoria
            self._assets_store[asset.id] = asset

            print("DEBUG: asset salvato in cache =", self._assets_store.get(asset.id))

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
        print("DEBUG: entro in get_asset")
        print("DEBUG: asset_id richiesto =", asset_id)

        self.log_debug(f"Recupero asset {asset_id} per Company {company_id}")

        asset: Asset | None = None

        # 1. Tentativo di lettura da Repository reale
        if self.asset_repo:
            try:
                asset = self.asset_repo.read(asset_id)
                print("DEBUG: asset letto da DB =", asset)
            except Exception as e:
                self.log_warning(
                    f"Impossibile leggere l'asset {asset_id} dal repository: {e}"
                )

        # 2. Fallback alla cache in memoria
        if not asset:
            asset = self._assets_store.get(asset_id)
            print("DEBUG: asset letto da cache =", asset)

        # 3. Verifica sicurezza Tenant (company_id)
        if not asset or asset.company_id != company_id:
            print("DEBUG: asset NON trovato o NON autorizzato")
            return None

        print("DEBUG: asset finale =", asset)
        return AssetMapper.to_dto(asset)

    def list_assets(self, company_id: str) -> list[AssetDTO]:
        """
        Elenca tutti gli asset appartenenti a una specifica azienda.
        """
        print("DEBUG: entro in list_assets")
        print("DEBUG: company_id richiesto =", company_id)

        self.log_info(f"Elenco asset per Company: {company_id}")

        company_assets: list[Asset] = []

        if self.asset_repo:
            try:
                all_assets = self.asset_repo.list_all()
                print("DEBUG: tutti gli asset dal DB =", all_assets)

                company_assets = [
                    a
                    for a in all_assets
                    if getattr(a, "company_id", None) == company_id
                ]
                print("DEBUG: asset filtrati per company =", company_assets)

            except Exception as e:
                self.log_error("Errore recupero lista asset dal repository", e)
                company_assets = [
                    a for a in self._assets_store.values() if a.company_id == company_id
                ]
                print("DEBUG: asset presi dalla cache =", company_assets)
        else:
            company_assets = [
                a for a in self._assets_store.values() if a.company_id == company_id
            ]
            print("DEBUG: asset presi dalla cache (repo assente) =", company_assets)

        # Utilizza il mapper per convertire la lista in DTO
        print("DEBUG: asset prima del mapping =", company_assets)

        if hasattr(AssetMapper, "to_dtos"):
            result = AssetMapper.to_dtos(company_assets)
            print("DEBUG: asset DTO finali =", result)
            return result

        result = [AssetMapper.to_dto(a) for a in company_assets]
        print("DEBUG: asset DTO finali =", result)
        return result

    def update_asset_risk(
        self, asset_id: str, company_id: str, new_risk_value: float
    ) -> AssetDTO:
        """
        Aggiorna il punteggio di rischio di un asset specifico.
        """
        print("DEBUG: entro in update_asset_risk")
        print("DEBUG: asset_id =", asset_id, "nuovo rischio =", new_risk_value)

        # Validazione e normalizzazione rigorosa del nuovo valore tramite RiscoScore Value Object
        try:
            val_rischio_float = (
                float(new_risk_value) if new_risk_value is not None else 0.0
            )
            score_obj = RiscoScore(val_rischio_float)
            validated_risk_value = score_obj.value
        except (InvalidRiscoScoreException, ValueError, TypeError):
            try:
                numeric_fallback = (
                    float(new_risk_value) if new_risk_value is not None else 0.0
                )
                clamped_val = max(0.0, min(10.0, numeric_fallback))
                validated_risk_value = RiscoScore(clamped_val).value
            except Exception:
                validated_risk_value = 0.0

        self.log_info(
            f"Aggiornamento rischio per asset {asset_id} -> Nuovo valore validato: {validated_risk_value}"
        )

        # 1. Recupera l'entità (da DB o cache)
        asset: Asset | None = None
        if self.asset_repo:
            try:
                asset = self.asset_repo.read(asset_id)
                print("DEBUG: asset letto da DB =", asset)
            except Exception:
                pass

        if not asset:
            asset = self._assets_store.get(asset_id)
            print("DEBUG: asset letto da cache =", asset)

        # 2. Verifica validità e sicurezza Tenant
        if not asset or asset.company_id != company_id:
            print("DEBUG: asset NON trovato o NON autorizzato")
            raise ValueError(
                f"Asset '{asset_id}' non trovato o non autorizzato per l'azienda {company_id}"
            )

        # 3. Applica modifica del rischio sull'entità di dominio
        if hasattr(asset, "aggiorna_rischio"):
            asset.aggiorna_rischio(validated_risk_value)
        elif hasattr(asset, "rischio"):
            asset.rischio = validated_risk_value

        print("DEBUG: asset dopo aggiornamento rischio =", asset)

        # 4. Salva sia sul Repository che nella cache
        if self.asset_repo:
            try:
                self.asset_repo.update(asset_id, asset)
                print("DEBUG: asset aggiornato nel DB")
            except Exception as e:
                self.log_error(
                    f"Errore durante l'aggiornamento dell'asset {asset_id} nel DB", e
                )

        self._assets_store[asset_id] = asset
        print("DEBUG: asset aggiornato in cache =", asset)

        return AssetMapper.to_dto(asset)

    def get_critical_assets(self, company_id: str) -> list[AssetDTO]:
        """
        Recupera soltanto gli asset contrassegnati come CRITICI per l'azienda.
        """
        print("DEBUG: entro in get_critical_assets")
        print("DEBUG: company_id =", company_id)

        self.log_info(f"Recupero asset critici per Company: {company_id}")
        all_assets = self.list_assets(company_id)
        critical = [a for a in all_assets if getattr(a, "is_critical", False)]

        print("DEBUG: asset critici =", critical)
        return critical

    def delete_asset(self, asset_id: str, company_id: str) -> bool:
        """
        Rimuove un asset sia dal repository che dalla cache locale.
        """
        print("DEBUG: entro in delete_asset")
        print("DEBUG: asset_id =", asset_id)

        self.log_info(f"Cancellazione asset {asset_id} per Company {company_id}")

        # Verifica esistenza
        asset_dto = self.get_asset(asset_id, company_id)
        print("DEBUG: asset da cancellare =", asset_dto)

        if not asset_dto:
            print("DEBUG: asset NON trovato, impossibile cancellare")
            return False

        # Rimuovi dal repository
        if self.asset_repo:
            try:
                self.asset_repo.delete(asset_id)
                print("DEBUG: asset cancellato dal DB")
            except Exception as e:
                self.log_error(
                    f"Errore durante la cancellazione dell'asset {asset_id} dal repository",
                    e,
                )

        # Rimuovi dalla cache
        self._assets_store.pop(asset_id, None)
        print("DEBUG: asset rimosso dalla cache")

        return True
