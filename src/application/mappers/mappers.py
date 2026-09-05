from __future__ import annotations

"""
Mappers - Conversione da Domain Entities a DTOs.
Responsabili della trasformazione dati tra layer.
"""

from src.application.dto import (
    AssetDiMercatoDTO,
    AssetDiValoreDTO,
    AssetDTO,
    RiskAnalysisDTO,
    UserDTO,
)
from src.domain import Asset, AssetDiMercato, AssetDiValore, Utente


class AssetMapper:
    """Mapper da Asset Domain a AssetDTO."""

    @staticmethod
    def to_dto(asset: Asset) -> AssetDTO:
        """
        Converte Asset domain a DTO.

        Args:
            asset: Domain entity

        Returns:
            AssetDTO pronto per presentazione
        """
        return AssetDTO(
            id=asset.id,
            nome=asset.nome,
            categoria=asset.categoria.value,
            rischio_value=asset.rischio.value,
            rischio_level=asset.rischio.level.value,
            momentum_status=asset.momentum.status.value,
            momentum_value=asset.momentum.value,
            volatilita_value=asset.volatilita.value,
            company_id=asset.company_id,
            data_creazione=asset.data_creazione.isoformat(),
            data_aggiornamento=asset.data_aggiornamento.isoformat(),
            is_critical=asset.is_critical,
            dati_extra=asset.dati_extra,
        )

    @staticmethod
    def to_dto_mercato(asset: AssetDiMercato) -> AssetDiMercatoDTO:
        """Converte AssetDiMercato a DTO."""
        base_dto = AssetMapper.to_dto(asset)
        return AssetDiMercatoDTO(
            **vars(base_dto),
            quantita=asset.quantita,
            sku=asset.sku,
            ubicazione=asset.ubicazione,
        )

    @staticmethod
    def to_dto_valore(asset: AssetDiValore) -> AssetDiValoreDTO:
        base_dto = AssetMapper.to_dto(asset)
        return AssetDiValoreDTO(
            **vars(base_dto),
            prezzo=asset.prezzo,
            stato_pagamento=asset.stato_pagamento,
            valuta=asset.valuta,
        )

    @staticmethod
    def to_dtos(assets: list[Asset]) -> list[AssetDTO]:
        """Converte lista asset a DTOs."""
        return [AssetMapper.to_dto(a) for a in assets]


class UserMapper:
    """Mapper da Utente Domain a UserDTO."""

    @staticmethod
    def to_dto(utente: Utente) -> UserDTO:
        """
        Converte Utente domain a DTO.

        Args:
            utente: Domain entity

        Returns:
            UserDTO
        """
        return UserDTO(
            id=utente.id,
            email=utente.email,
            ruolo=utente.ruolo,
            azienda_id=utente.azienda_id,
            data_creazione=utente.data_creazione.isoformat(),
            data_ultimo_login=(
                utente.data_ultimo_login.isoformat()
                if utente.data_ultimo_login
                else None
            ),
        )


class RiskAnalysisMapper:
    """Mapper per risultati analisi di rischio."""

    @staticmethod
    def to_dto(
        asset: Asset,
        rischio_attuale: float,
        rischio_30gg: float,
        rischio_60gg: float,
        rischio_90gg: float,
        trend: str,
        trend_value: float,
        consiglio: str,
        urgenza: str,
        confidenza: float = 0.85,
    ) -> RiskAnalysisDTO:
        """
        Crea DTO per analisi di rischio.
        """
        return RiskAnalysisDTO(
            asset_id=asset.id,
            asset_nome=asset.nome,
            rischio_attuale=rischio_attuale,
            rischio_proiezione_30gg=rischio_30gg,
            rischio_proiezione_60gg=rischio_60gg,
            rischio_proiezione_90gg=rischio_90gg,
            trend=trend,
            trend_value=trend_value,
            volatilita=asset.volatilita.value,
            consiglio_strategico=consiglio,
            urgenza=urgenza,
            confidenza=confidenza,
        )
