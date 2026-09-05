"""
Domain Constants - Enumerazioni e costanti di dominio.
"""

from enum import Enum


class AssetCategory(str, Enum):
    """Categorie di Asset nel sistema."""

    FINANCE = "FINANCE"
    LOGISTICS = "LOGISTICS"
    RELATIONS = "RELATIONS"
    GENERAL = "GENERAL"


class MomentumStatus(str, Enum):
    """Stato del momentum (accelerazione/decelerazione rischio)."""

    ACCELERATING = "ACCELERATING"  # Rischio in aumento
    DECELERATING = "DECELERATING"  # Rischio in diminuzione
    STABLE = "STABLE"  # Rischio stabile
    UNDEFINED = "UNDEFINED"  # Non ancora calcolato


class RiskLevel(str, Enum):
    """Livelli di rischio."""

    CRITICAL = "CRITICAL"  # >= 7.5
    WARNING = "WARNING"  # 5.0 - 7.5
    SAFE = "SAFE"  # < 5.0


class PaymentStatus(str, Enum):
    """Stato di pagamento (per AssetDiValore)."""

    PAID = "PAID"
    PENDING = "PENDING"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"


class InventoryStatus(str, Enum):
    """Stato inventario (per AssetDiMercato)."""

    IN_STOCK = "IN_STOCK"
    LOW_STOCK = "LOW_STOCK"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    DAMAGED = "DAMAGED"


class UserRole(str, Enum):
    """Ruoli utente nel sistema."""

    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"


# ========== MAPPATURE SINONIMI ==========
# Usate dall'ingestor per riconoscere colonne da file ERP diversi

SINONIMI_MAPPING: dict[str, list[str]] = {
    "quantita": [
        "quantita",
        "pezzi",
        "qta",
        "stock",
        "unita",
        "giacenza",
        "quantity",
        "vol",
        "qty",
        "menge",
    ],
    "valore": [
        "prezzo",
        "importo",
        "lordo",
        "valore",
        "costo",
        "ammontare",
        "costo_unitario",
        "prezzo_acquisto",
        "amount",
        "price",
        "netwr",
        "dmbtr",
    ],
    "rischio": [
        "rischio",
        "impatto",
        "criticita",
        "priorita",
        "rischio_logistico",
        "risk_factor",
        "risk",
        "score",
    ],
    "stato": [
        "stato",
        "condizione",
        "status",
        "pagamento",
        "disponibilita",
        "stato_qualita",
        "level",
    ],
    "id_asset": ["codice", "id", "reference", "ref", "belnr", "matnr", "id_asset"],
    "nome": ["descrizione", "prodotto", "materiale", "item", "nome", "asset", "maktx"],
}

# ========== SAP FIELD MAPPING ==========
SAP_FIELD_MAPPING: dict[str, list[str]] = {
    "quantita": ["menge", "labst", "vclog"],
    "valore": ["netwr", "dmbtr", "waers", "knumv"],
    "nome": ["matnr", "maktx", "arktx"],
    "id_asset": ["belnr", "vbeln", "aufnr"],
}

# ========== SETTORE KEYS ==========
# Usate per riconoscere il settore dal file

SETTORE_KEYS: dict[str, list[str]] = {
    "FINANCE": ["fattura", "iban", "lordo", "costo_unitario", "netwr", "dmbtr"],
    "LOGISTICS": [
        "bolla",
        "ddt",
        "magazzino",
        "quantita",
        "sku",
        "matnr",
        "menge",
        "labst",
    ],
    "RELATIONS": ["cliente", "fornitore", "crm", "kunnr", "lifnr"],
}
