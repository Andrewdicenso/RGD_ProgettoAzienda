# src/application/services/asset_service.py
"""
Asset Service - Use Case: Gestione Lifecycle Asset.
Orchestra la creazione, il recupero, la modifica del rischio e la rimozione
degli asset aziendali tramite Repository e Cache locale.
Integrato con AIProvider (Groq Ultra motore principale, Gemini validator gratuito)
per arricchimenti opzionali, suggerimenti operativi e validazione testuale.
"""

import logging
from typing import TYPE_CHECKING, Any

from src.application.dto import AssetDTO
from src.application.mappers import AssetMapper
from src.application.services.base_service import BaseService
from src.domain import Asset
from src.domain.exceptions import InvalidRiscoScoreException
from src.domain.value_objects import RiscoScore

if TYPE_CHECKING:
    # The optional AI provider dependency may not exist in all environments.
    # Use a permissive fallback for static analysis so IDEs do not report a
    # missing import when the dependency is intentionally optional.
    AIProvider = Any  # type: ignore[assignment]
else:
    try:
        from src.infrastructure.external.providers.ai_provider import AIProvider
    except ImportError:  # pragma: no cover - dipendenza opzionale
        AIProvider = Any  # type: ignore[assignment]

logger = logging.getLogger("RGD-Alpha.AssetService")


class AssetService(BaseService):
    """
    Servizio per la gestione degli asset.
    Orchestra le operazioni sugli asset garantendo la sicurezza multi-tenant (company_id).
    Integra AIProvider in modo opzionale: se presente, viene usato per arricchire descrizioni,
    generare suggerimenti operativi e validare/raffinare testi.
    """

    def __init__(
        self, asset_repo: Any | None = None, ai_provider: AIProvider | None = None
    ):
        """Inizializza AssetService con il repository (Dependency Injection)."""
        super().__init__("AssetService")
        self.asset_repo = asset_repo
        self.ai_provider: AIProvider | None = ai_provider
        self._assets_store: dict[str, Asset] = {}  # Cache/Backup in memoria

    def _ai_enrich_asset(self, asset: Asset) -> None:
        """
        Chiamata opzionale all'AI per arricchire l'asset (es. descrizione sintetica,
        tag, priorità testuale). Non fallisce la pipeline: in caso di errore si ignora.
        """
        if not self.ai_provider:
            return

        try:
            # Costruisco un prompt sintetico per generare una breve descrizione e tag
            prompt = (
                f"Genera una breve descrizione professionale (max 2 frasi) e 3 tag "
                f"separati da virgola per questo asset:\nNome: {getattr(asset, 'nome', '')}\n"
                f"Categoria: {getattr(asset, 'categoria', '')}\n"
                f"Rischio: {getattr(asset, 'rischio', '')}\n"
            )
            if hasattr(self.ai_provider, "generate_advice"):
                ai_out = self.ai_provider.generate_advice(prompt)
            elif hasattr(self.ai_provider, "analyze"):
                ai_out = self.ai_provider.analyze(
                    {
                        "asset": AssetMapper.to_dto(asset),
                        "instructions": "breve descrizione e 3 tag",
                    }
                )
            else:
                ai_out = None

            if ai_out:
                # Provo a parsare in modo semplice: prima riga = descrizione, seconda = tag
                lines = [l.strip() for l in str(ai_out).splitlines() if l.strip()]
                if lines:
                    descr = lines[0]
                    asset.descrizione_ai = descr
                if len(lines) > 1:
                    tags_line = lines[1]
                    asset.tags_ai = [
                        t.strip() for t in tags_line.split(",") if t.strip()
                    ]
        except Exception as e:
            logger.debug(
                "AI enrichment failed for asset %s: %s",
                getattr(asset, "id", "unknown"),
                e,
            )

    def create_asset(self, asset: Asset) -> AssetDTO:
        """
        Salva o registra un nuovo asset per l'azienda.
        Mantiene la validazione RiscoScore e aggiunge arricchimenti AI opzionali.
        """
        logger.debug("create_asset: asset ricevuto = %s", asset)

        # Validazione e normalizzazione robusta del rischio tramite RiscoScore Value Object
        if hasattr(asset, "rischio") and asset.rischio is not None:
            try:
                if isinstance(asset.rischio, RiscoScore):
                    pass
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

        # Arricchimento AI opzionale (non bloccante)
        self._ai_enrich_asset(asset)

        self.log_info(
            f"Salvataggio asset '{asset.nome}' (ID: {asset.id}) per Company: {asset.company_id}"
        )
        try:
            # 1. Persistenza su database (Repository)
            if self.asset_repo:
                self.asset_repo.create(asset)

            # 2. Aggiornamento cache in memoria
            self._assets_store[asset.id] = asset

            logger.debug(
                "asset salvato in cache = %s", self._assets_store.get(asset.id)
            )
            return AssetMapper.to_dto(asset)
        except Exception as e:
            self.log_error(
                f"Errore durante il salvataggio dell'asset '{getattr(asset, 'nome', asset.id)}'",
                e,
            )
            raise

    def get_asset(self, asset_id: str, company_id: str) -> AssetDTO | None:
        """
        Recupera un asset specifico verificando la proprietà della company.
        """
        logger.debug("get_asset: asset_id richiesto = %s", asset_id)

        asset: Asset | None = None

        # 1. Tentativo di lettura da Repository reale
        if self.asset_repo:
            try:
                asset = self.asset_repo.read(asset_id)
                logger.debug("asset letto da DB = %s", asset)
            except Exception as e:
                self.log_warning(
                    f"Impossibile leggere l'asset {asset_id} dal repository: {e}"
                )

        # 2. Fallback alla cache in memoria
        if not asset:
            asset = self._assets_store.get(asset_id)
            logger.debug("asset letto da cache = %s", asset)

        # 3. Verifica sicurezza Tenant (company_id)
        if not asset or getattr(asset, "company_id", None) != company_id:
            logger.debug("asset NON trovato o NON autorizzato")
            return None

        logger.debug("asset finale = %s", asset)
        return AssetMapper.to_dto(asset)

    def list_assets(self, company_id: str) -> list[AssetDTO]:
        """
        Elenca tutti gli asset appartenenti a una specifica azienda.
        """
        logger.debug("list_assets: company_id richiesto = %s", company_id)
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
        Se disponibile, chiede all'AIProvider un consiglio operativo sintetico da allegare all'asset.
        """
        logger.debug(
            "update_asset_risk: asset_id=%s nuovo rischio=%s", asset_id, new_risk_value
        )

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
                logger.debug("asset letto da DB = %s", asset)
            except Exception:
                pass

        if not asset:
            asset = self._assets_store.get(asset_id)
            logger.debug("asset letto da cache = %s", asset)

        # 2. Verifica validità e sicurezza Tenant
        if not asset or getattr(asset, "company_id", None) != company_id:
            logger.debug("asset NON trovato o NON autorizzato")
            raise ValueError(
                f"Asset '{asset_id}' non trovato o non autorizzato per l'azienda {company_id}"
            )

        # 3. Applica modifica del rischio sull'entità di dominio
        if hasattr(asset, "aggiorna_rischio"):
            asset.aggiorna_rischio(validated_risk_value)
        elif hasattr(asset, "rischio"):
            asset.rischio = validated_risk_value

        logger.debug("asset dopo aggiornamento rischio = %s", asset)

        # 4. Se disponibile, chiedi all'AI un consiglio operativo sintetico (non bloccante)
        if self.ai_provider:
            try:
                prompt = (
                    f"Asset: {getattr(asset, 'nome', '')}\n"
                    f"Rischio aggiornato: {validated_risk_value}\n"
                    "Genera un consiglio operativo sintetico (1-2 frasi) per mitigare il rischio."
                )
                if hasattr(self.ai_provider, "generate_advice"):
                    advice = self.ai_provider.generate_advice(prompt)
                elif hasattr(self.ai_provider, "analyze"):
                    advice = self.ai_provider.analyze(
                        {
                            "asset": AssetMapper.to_dto(asset),
                            "instructions": "consiglio operativo sintetico",
                        }
                    )
                else:
                    advice = None

                if advice:
                    # Salvo il consiglio nell'asset come metadato non invasivo
                    asset.consiglio_ai = advice
            except Exception as e:
                logger.debug(
                    "AI advice generation failed for asset %s: %s", asset_id, e
                )

        # 5. Salva sia sul Repository che nella cache
        if self.asset_repo:
            try:
                self.asset_repo.update(asset_id, asset)
                logger.debug("asset aggiornato nel DB")
            except Exception as e:
                self.log_error(
                    f"Errore durante l'aggiornamento dell'asset {asset_id} nel DB", e
                )

        self._assets_store[asset_id] = asset
        logger.debug("asset aggiornato in cache = %s", asset)

        return AssetMapper.to_dto(asset)

    def get_critical_assets(self, company_id: str) -> list[AssetDTO]:
        """
        Recupera soltanto gli asset contrassegnati come CRITICI per l'azienda.
        Se disponibile, chiede all'AI un breve sommario operativo aggregato.
        """
        self.log_info(f"Recupero asset critici per Company: {company_id}")
        all_assets = self.list_assets(company_id)
        critical = [a for a in all_assets if getattr(a, "is_critical", False)]

        # Opzionale: generare un sommario operativo aggregato via AI (non bloccante)
        if self.ai_provider and critical:
            try:
                assets_brief = [
                    {
                        "id": a.id,
                        "nome": getattr(a, "nome", ""),
                        "rischio": getattr(a, "rischio", ""),
                    }
                    for a in critical
                ]
                prompt = f"Genera un breve sommario operativo per questi asset critici: {assets_brief}"
                if hasattr(self.ai_provider, "analyze"):
                    summary = self.ai_provider.analyze(
                        {
                            "assets": assets_brief,
                            "instructions": "sommario operativo in 3 bullet points",
                        }
                    )
                elif hasattr(self.ai_provider, "generate_advice"):
                    summary = self.ai_provider.generate_advice(prompt)
                else:
                    summary = None

                if summary:
                    # allego il sommario al primo asset come metadato (non invasivo)
                    critical[0].sommario_critici_ai = summary
            except Exception as e:
                logger.debug("AI summary for critical assets failed: %s", e)

        return critical

    def delete_asset(self, asset_id: str, company_id: str) -> bool:
        """
        Rimuove un asset sia dal repository che dalla cache locale.
        """
        self.log_info(f"Cancellazione asset {asset_id} per Company {company_id}")

        asset_dto = self.get_asset(asset_id, company_id)
        if not asset_dto:
            logger.debug("asset NON trovato, impossibile cancellare")
            return False

        # Rimuovi dal repository
        if self.asset_repo:
            try:
                self.asset_repo.delete(asset_id)
                logger.debug("asset cancellato dal DB")
            except Exception as e:
                self.log_error(
                    f"Errore durante la cancellazione dell'asset {asset_id} dal repository",
                    e,
                )

        # Rimuovi dalla cache
        self._assets_store.pop(asset_id, None)
        logger.debug("asset rimosso dalla cache")
        return True
