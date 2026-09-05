# 🏗️ RGD-Alpha Refactorizzazione - Guida Implementazione

## 📋 **Stato Implementazione**

Questa è la **FASE 1+2+5** della refactorizzazione:

✅ **FASE 1: Foundation + Config**
- ✅ `src/config/settings.py` - Configurazione centralizzata
- ✅ `src/config/di_container.py` - Dependency Injection
- ✅ `.env.example` - Template variabili d'ambiente

✅ **FASE 2: Domain Layer (Logica Pura)**
- ✅ `src/domain/entities.py` - Asset, Azienda, Utente (logica pura)
- ✅ `src/domain/value_objects.py` - RiscoScore, Momentum, Volatilita
- ✅ `src/domain/exceptions.py` - Eccezioni di dominio
- ✅ `src/domain/constants.py` - Enumerazioni e costanti

✅ **FASE 5: Presentation Layer (UI)**
- ✅ `src/presentation/streamlit_app.py` - App main refactorizzata
- ✅ `src/presentation/state/session_manager.py` - Gestione stato Streamlit
- ✅ `src/presentation/components/auth_forms.py` - Form autenticazione
- ✅ `src/presentation/pages/0_home.py` - Homepage placeholder
- ✅ `tests/conftest.py` - Setup pytest
- ✅ `tests/test_domain_entities.py` - Test di esempio

⏳ **DA FARE (FASE 3+4+6):**
- [ ] FASE 3: Application Services (AssetService, AnalysisService, etc.)
- [ ] FASE 4: Infrastructure (Repositories, Database, Security)
- [ ] FASE 6: Test completi e CI/CD

---

## 🚀 **Come Usare Questa Refactorizzazione**

### **1. Installa Dipendenze**

```bash
# Crea virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Installa dipendenze
pip install -r requirements.txt
pip install pytest pytest-cov  # Per test
```

### **2. Configura Variabili d'Ambiente**

```bash
# Copia il template
cp .env.example .env

# Modifica .env con le tue credenziali
# ADMIN_EMAIL=andrewdicenso@libero.it
# GROQ_API_KEY=your-key-here
# ...
```

### **3. Avvia l'App Refactorizzata**

```bash
# Avvia la nuova app refactorizzata
streamlit run src/presentation/streamlit_app.py
```

**Credenziali Demo:**
- Email: `andrewdicenso@libero.it`
- Password: `WarRoom123!`

### **4. Esegui Test di Esempio**

```bash
# Esegui test domain
pytest tests/test_domain_entities.py -v

# Esegui tutti i test
pytest tests/ -v

# Con coverage
pytest tests/ --cov=src --cov-report=html
```

---

## 📐 **Struttura Nuova vs Vecchia**

### **Vecchia Struttura (app.py monolitico)**
```
app.py                    ← TUTTO QUI (1000+ righe)
src/
  database.py            ← Mixed logic + persistence
  engine.py              ← Mixed logic
  analyst.py             ← Mixed logic
auth/
  auth.py                ← Login logic
```

### **Nuova Struttura (Clean Architecture)**
```
src/
├── config/              ← CONFIGURAZIONE CENTRALIZZATA
│   ├── settings.py      ← Tutte le config in un posto
│   └── di_container.py  ← Dependency Injection
│
├── domain/              ← LOGICA PURA (NO Database, NO Streamlit)
│   ├── entities.py      ← Asset, Azienda, Utente (con métodi di business)
│   ├── value_objects.py ← RiscoScore, Momentum (logica incapsulata)
│   ├── exceptions.py    ← Eccezioni di dominio
│   └── constants.py     ← Enum, costanti, mappature
│
├── application/         ← ORCHIESTRAZIONE (Implementation later)
│   ├── services/        ← AssetService, AnalysisService, etc.
│   ├── dto/             ← Data Transfer Objects
│   └── mappers/         ← Domain → DTO conversion
│
├── infrastructure/      ← DETTAGLI TECNICI (Implementation later)
│   ├── persistence/     ← Database, Repositories
│   ├── security/        ← Vault, Crypto
│   └── external/        ← Gmail, SFTP, LLM APIs
│
└── presentation/        ← USER INTERFACE
    ├── streamlit_app.py ← Entry point (SEMPLICE!)
    ├── pages/           ← Multi-page Streamlit
    ├── components/      ← UI components riusabili
    └── state/           ← Session management

tests/                   ← TEST SUITE
├── conftest.py         ← Fixtures
├── test_domain_entities.py ← Test di esempio
└── unit/               ← Unit test
```

---

## 🔄 **Flusso di Dati (Nuovo)**

```
USER INPUT (Form)
    ↓
VALIDATION (src/presentation/components/)
    ↓
SESSION STATE (SessionManager)
    ↓
[FUTURE] SERVICE CALL (src/application/services/)
    ↓
DOMAIN LOGIC (src/domain/entities/)
    ↓
[FUTURE] REPOSITORY SAVE (src/infrastructure/persistence/)
    ↓
RESPONSE (DTO)
    ↓
UI RENDER (src/presentation/)
```

---

## 💡 **Cosa È Cambiato?**

### **Prima (Vecchio app.py)**
```python
# app.py - 500 righe di mix di UI + Business Logic + Database
import streamlit as st
from src.database import DatabaseAziendale

db = DatabaseAziendale()

if st.button("Login"):
    user = db.get_utente_by_email(email)  # Business logic qua?
    if bcrypt.checkpw(...):  # Crypto qua?
        st.session_state.autenticato = True  # State management improvvisato
```

### **Dopo (Nuovo streamlit_app.py)**
```python
# src/presentation/streamlit_app.py - SEMPLICE, solo UI logic
from src.config import get_settings
from src.presentation.state import SessionManager
from src.presentation.components import render_login_tabs


def handle_login(email: str, password: str) -> bool:
    # TODO: Chiama AuthService quando implementato
    # Per ora, solo placeholder
    pass


if SessionManager.is_autenticato():
    render_app_pages()
else:
    render_auth_pages()
```

**Vantaggi:**
- ✅ UI logic separata da Business logic
- ✅ Facile testare (domain logic ha zero dipendenze)
- ✅ Facile aggiungere feature (ogni layer è indipendente)
- ✅ Facile debugging (errori localizzati)

---

## 🧪 **Test - Come Funzionano**

Guarda `tests/test_domain_entities.py` per esempi:

```python
# Test delle value objects (logica incapsulata)
def test_risco_score_valido():
    score = RiscoScore(5.5)
    assert score.is_warning is True  # ✅ Logica pura, no database

# Test delle entity
def test_crea_asset():
    asset = Asset(nome="Test", company_id="test")
    assert asset.is_critical is False  # ✅ Métodi di business

# Run test
pytest tests/test_domain_entities.py -v
```

---

## 📝 **Prossimi Step (FASE 3+4)**

### **FASE 3: Application Services** (When ready)
Implement:
```python
src/application/services/
├── asset_service.py      # UseCase: Gestione Asset
├── analysis_service.py   # UseCase: Analisi Rischio
├── ingestion_service.py  # UseCase: Caricamento Dati
└── auth_service.py       # UseCase: Autenticazione
```

### **FASE 4: Infrastructure** (When ready)
Implement:
```python
src/infrastructure/
├── persistence/repositories/  # Database access (Repository pattern)
├── security/vault.py          # Crittografia
└── external/                  # API esterne (Gmail, SFTP, Groq)
```

### **FASE 6: Testing Completo**
Add:
```
tests/unit/              # Unit test per services
tests/integration/       # Integration test
tests/e2e/              # End-to-end test
```

---

## ⚠️ **IMPORTANTISSIMO - Non toccare ancora**

❌ **NON MODIFICARE** (ancora accoppiati a vecchio codice):
- `app.py` (vecchio entry point)
- `src/` (vecchio monolith)
- `auth/` (vecchio auth)

✅ **USA SOLO** (nuova struttura):
- `src/` (nuova struttura)
- `tests/` (nuovi test)

**Strategy:**
1. Testa la nuova app nel branch `refactor/foundation`
2. Quando pronto, migra `src/` → `src/infrastructure/`
3. Infine, elimina vecchio `app.py`

---

## 🐛 **Troubleshooting**

### **Import errors?**
```python
# Assicurati di avere i __init__.py in ogni cartella
# Esempio:
src / __init__.py
src / config / __init__.py
src / domain / __init__.py
src / presentation / __init__.py
```

### **App non avvia?**
```bash
# Verifica percorsi
python -c "from src.config import get_settings; print('OK')"

# Verifica Streamlit
streamlit run src/presentation/streamlit_app.py --logger.level=debug
```

### **Test falliscono?**
```bash
# Installa dipendenze test
pip install pytest pytest-cov

# Run test con verbose
pytest tests/test_domain_entities.py -vv -s
```

---

## 📚 **Documentazione Aggiuntiva**

Vedi anche (quando implementate):
- `docs/ARCHITECTURE.md` - Architettura completa
- `docs/API.md` - API services
- `docs/DATABASE.md` - Schema database
- `docs/TESTING.md` - Strategie testing

---

## ✅ **Checklist per Validare**

Prima di mergiare nel main:

- [ ] App avvia senza errori
- [ ] Login funziona (con credenziali demo)
- [ ] Tests passano: `pytest tests/ -v`
- [ ] Linting OK: `flake8 src/`
- [ ] Type hints OK: `mypy src/ --strict`
- [ ] Documentazione updated

---

## 🤝 **Domande?**

Se hai problemi o dubbi:
1. Guarda i test di esempio: `tests/test_domain_entities.py`
2. Controlla la struttura: `tree src/`
3. Leggi i docstring: every function ha docstring
4. Apri un issue o chiedi aiuto

---

**Happy Refactoring! 🚀**
