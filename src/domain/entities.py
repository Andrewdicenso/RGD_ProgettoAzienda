"""
Domain Entities - Entità di Business RGD-Alpha.
Logica pura del dominio (no database, no external calls).
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .constants import AssetCategory, MomentumStatus
from .exceptions import InvalidAssetException
from .value_objects import Momentum, RiscoScore, Volatilita


@dataclass
class Asset:
    """
    Entità Base: Asset Generico.
    Ogni Asset ha un rischio, è monitorato nel tempo, ha metadata.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    nome: str = ""
    company_id: str = ""
    rischio: RiscoScore = field(default_factory=lambda: RiscoScore(0.0))
    momentum: Momentum = field(
        default_factory=lambda: Momentum(MomentumStatus.UNDEFINED, 0.0)
    )
    volatilita: Volatilita = field(default_factory=lambda: Volatilita(0.0))
    categoria: AssetCategory = AssetCategory.GENERAL
    data_creazione: datetime = field(default_factory=datetime.now)
    data_aggiornamento: datetime = field(default_factory=datetime.now)
    dati_extra: dict[str, Any] = field(default_factory=dict)

    @property
    def azienda_id(self):
        """Rende l'asset compatibile con le chiamate che usano 'azienda_id'"""
        return self.company_id

    @azienda_id.setter
    def azienda_id(self, value):
        self.company_id = value

    def __post_init__(self):
        """Validazione al momento della creazione."""
        if not self.nome:
            raise InvalidAssetException("Asset nome non può essere vuoto")
        if not self.company_id:
            raise InvalidAssetException("Asset company_id non può essere vuoto")

    @property
    def is_critical(self) -> bool:
        """Vero se asset richiede intervento immediato."""
        return self.rischio.is_critical

    @property
    def is_warning(self) -> bool:
        """Vero se asset in stato di avvertenza."""
        return self.rischio.is_warning

    def aggiorna_rischio(self, nuovo_rischio: float) -> None:
        """Aggiorna il punteggio di rischio."""
        self.rischio = RiscoScore(nuovo_rischio)
        self.data_aggiornamento = datetime.now()

    def aggiorna_momentum(self, status: MomentumStatus, value: float) -> None:
        """Aggiorna il momentum."""
        self.momentum = Momentum(status, value)
        self.data_aggiornamento = datetime.now()

    def __str__(self) -> str:
        return f"Asset({self.nome} | {self.categoria.value} | {self.rischio})"


@dataclass
class AssetDiMercato(Asset):
    """
    Asset di Mercato - LOGISTICA & MAGAZZINO.
    Traccia inventario, SKU, ubicazioni.
    """

    categoria: AssetCategory = AssetCategory.LOGISTICS
    quantita: float = 0.0
    sku: str = ""
    ubicazione: str = "Magazzino Centrale"

    def __post_init__(self):
        """Validazione asset logistica."""
        super().__post_init__()
        if self.quantita < 0:
            raise InvalidAssetException(
                f"Quantità non può essere negativa: {self.quantita}"
            )


@dataclass
class AssetDiValore(Asset):
    """
    Asset di Valore - FINANCE & CONTABILITÀ.
    Traccia prezzi, importi, stati di pagamento.
    """

    categoria: AssetCategory = AssetCategory.FINANCE
    prezzo: float = 0.0
    stato_pagamento: str = "In attesa"
    valuta: str = "EUR"

    def __post_init__(self):
        """Validazione asset finanziario."""
        super().__post_init__()
        if self.prezzo < 0:
            raise InvalidAssetException(
                f"Prezzo non può essere negativo: {self.prezzo}"
            )


@dataclass
class AssetDiRelazione(Asset):
    """
    Asset di Relazione - CRM & RELAZIONI COMMERCIALI.
    Traccia partner, fornitori, clienti, livelli di servizio.
    """

    categoria: AssetCategory = AssetCategory.RELATIONS
    partner: str = "Privato"
    livello_servizio: float = 5.0

    def __post_init__(self):
        """Validazione asset relazionale."""
        super().__post_init__()
        if not (0 <= self.livello_servizio <= 10):
            raise InvalidAssetException(
                f"Livello servizio deve essere 0-10: {self.livello_servizio}"
            )


@dataclass
class Azienda:
    """
    Entità Azienda - Aggregato Root.
    Rappresenta un'azienda cliente nel sistema multi-tenant.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    nome: str = ""
    partita_iva: str = ""
    settore: str = ""
    owner_email: str = ""
    data_creazione: datetime = field(default_factory=datetime.now)
    assets: dict[str, Asset] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validazione azienda."""
        if not self.nome:
            raise InvalidAssetException("Azienda nome non può essere vuoto")

    def aggiungi_asset(self, asset: Asset) -> None:
        """Aggiungi un asset all'azienda."""
        asset.company_id = self.id
        self.assets[asset.id] = asset

    def rimuovi_asset(self, asset_id: str) -> None:
        """Rimuovi un asset dall'azienda."""
        self.assets.pop(asset_id, None)

    def recupera_asset(self, asset_id: str) -> Asset | None:
        """Recupera un asset per ID."""
        return self.assets.get(asset_id)

    def asset_critici(self) -> list[Asset]:
        """Ritorna lista asset critici."""
        return [a for a in self.assets.values() if a.is_critical]

    def __str__(self) -> str:
        return f"Azienda({self.nome} | {len(self.assets)} assets)"


@dataclass
class Utente:
    """
    Entità Utente - Aggregato Root.
    Rappresenta un utente nel sistema.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    email: str = ""
    password_hash: str = ""
    ruolo: str = "user"
    azienda_id: str | None = None
    data_creazione: datetime = field(default_factory=datetime.now)
    data_ultimo_login: datetime | None = None

    def __post_init__(self):
        """Validazione utente."""
        if not self.email:
            raise InvalidAssetException("Utente email non può essere vuota")
        if not self.password_hash:
            raise InvalidAssetException("Utente password_hash non può essere vuota")

    @property
    def is_admin(self) -> bool:
        """Vero se l'utente è amministratore."""
        return self.ruolo == "admin"

    def __str__(self) -> str:
        return f"Utente({self.email} | {self.ruolo})"


# ========== HELPER FACTORIES ==========


def crea_asset_dal_dizionario(data: dict[str, Any], categoria: AssetCategory) -> Asset:
    """
    Factory function: crea un Asset dal dizionario.
    Risolve il conflitto tra azienda_id e company_id e supporta nomi colonne vari.
    """
    asset_id = data.get("id", str(uuid.uuid4()))

    # Prova a prendere il nome in vari modi (italiano/inglese/maiuscolo)
    nome = data.get("nome", data.get("Nome", "Asset Senza Nome"))

    # RISOLUZIONE CRITICA: Cerca l'ID azienda in ogni formato possibile
    company_id = data.get(
        "company_id", data.get("azienda_id", data.get("Company_ID", ""))
    )

    # Prova a leggere il rischio
    rischio_value = float(data.get("rischio", data.get("Rischio", 0.0)))

    common_kwargs = {
        "id": asset_id,
        "nome": nome,
        "company_id": company_id,
        "rischio": RiscoScore(rischio_value),
        "dati_extra": data,
    }

    if categoria == AssetCategory.LOGISTICS:
        return AssetDiMercato(
            quantita=data.get("quantita", 0.0),
            sku=data.get("sku", ""),
            ubicazione=data.get("ubicazione", ""),
            **common_kwargs,
        )
    elif categoria == AssetCategory.FINANCE:
        return AssetDiValore(
            prezzo=data.get("prezzo", 0.0),
            stato_pagamento=data.get("stato_pagamento", ""),
            valuta=data.get("valuta", "EUR"),
            **common_kwargs,
        )
    elif categoria == AssetCategory.RELATIONS:
        return AssetDiRelazione(
            partner=data.get("partner", ""),
            livello_servizio=data.get("livello_servizio", 5.0),
            **common_kwargs,
        )
    else:
        return Asset(**common_kwargs)
