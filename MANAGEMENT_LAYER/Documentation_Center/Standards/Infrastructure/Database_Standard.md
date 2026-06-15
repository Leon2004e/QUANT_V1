# DATABASE STANDARD

Layer: Infrastructure  
Status: Active  
Version: 1.0  
Owner: Leon Everts  
System: QUANT OS

---

# PURPOSE

Der Database Standard definiert, wie strukturierte Daten innerhalb von QUANT OS gespeichert, getrennt, versioniert, gesichert und genutzt werden.

Datenbanken sind verantwortlich für:

- strukturierte Informationen
- Metadaten
- Registries
- Statusinformationen
- Referenzen
- Konfigurationen
- Events
- Audit Trails
- Trade-Historien
- Marktdaten in standardisierter Form
- Monitoring-Zustände

Datenbanken speichern keine großen Rohdateien.

Große Exporte, CSV-Dateien, Backtests, Reports und Rohdaten gehören in Storage.

---

# CORE PRINCIPLE

```text
Storage = Dateien

Databases = strukturierte Informationen

Control Plane = zentrale Systemsteuerung

Backend = Verarbeitung

Frontend = Visualisierung
```

Keine Datenbank darf unklare Mischverantwortung haben.

Jede Datenbank muss eine klar definierte Aufgabe besitzen.

---

# DATABASE STRUCTURE

```text
QUANT_OS/
└── Infrastructure/
    └── Databases/
```

Operativ genutzte Datenbanken liegen je nach Layer zusätzlich an ihrem fachlichen Ort.

Empfohlene Struktur:

```text
QUANT_OS/
│
├── CONTROL_PLANE/
│   └── Database/
│       └── QUANT_SYSTEM.db
│
├── Backend/
│   └── Data_Center/
│       └── Databases/
│           ├── Trade_History.db
│           ├── Market_Data.db
│           ├── Monitoring.db
│           └── Audit.db
│
└── Management/
    └── Documentation_Center/
        └── Standards/
            └── Infrastructure/
                └── Database_Standard.md
```

---

# DATABASE INVENTORY

QUANT OS nutzt folgende Hauptdatenbanken:

```text
QUANT_SYSTEM.db
Trade_History.db
Market_Data.db
Monitoring.db
Audit.db
```

---

# 1. QUANT_SYSTEM.DB

## Zweck

`QUANT_SYSTEM.db` ist die zentrale Control-Plane-Datenbank.

Sie speichert den aktuellen Systemzustand und die zentralen Referenzen des QUANT OS.

Sie ist das Gehirn des Systems.

## Speichert

- Strategien
- Portfolios
- Portfolio-Mitglieder
- Accounts
- Deployments
- Risk Limits
- Governance Rules
- System Events
- Audit Referenzen
- aktuelle Lifecycle-Zustände
- aktuelle Scores
- Statusinformationen

## Speichert NICHT

- Tickdaten
- OHLC-Daten
- große Backtest-Dateien
- große CSV-Dateien
- vollständige Trade-Historien
- Rohdaten
- Reports

## Tabellen v1

```text
QUANT_SYSTEM.db
│
├── strategies
├── portfolios
├── portfolio_members
├── accounts
├── deployments
├── risk_limits
├── governance_rules
├── system_events
├── audit_logs
└── schema_migrations
```

## strategies

Zweck:

Speichert alle registrierten Strategien.

Pflichtfelder:

```text
strategy_id
strategy_name
version
status
lifecycle
score
created_at
updated_at
```

Beispiel:

```text
strategy_id: EA_145
strategy_name: GBPJPY Trend Breakout
version: v4
status: active
lifecycle: HOT
score: 91
```

## portfolios

Zweck:

Speichert alle Portfolios.

Pflichtfelder:

```text
portfolio_id
portfolio_name
status
created_at
updated_at
```

## portfolio_members

Zweck:

Verbindet Strategien mit Portfolios.

Pflichtfelder:

```text
portfolio_id
strategy_id
weight
status
created_at
updated_at
```

## accounts

Zweck:

Speichert alle Accounts.

Pflichtfelder:

```text
account_id
broker
account_type
balance
status
created_at
updated_at
```

Erlaubte account_type Werte:

```text
DEMO
LIVE
PROP
BACKTEST
```

## deployments

Zweck:

Speichert, welche Strategie auf welchem Account in welcher Version läuft.

Pflichtfelder:

```text
deployment_id
strategy_id
account_id
version
status
started_at
stopped_at
created_at
updated_at
```

Erlaubte status Werte:

```text
planned
running
paused
stopped
failed
retired
```

## risk_limits

Zweck:

Speichert Risikolimits pro Account.

Pflichtfelder:

```text
account_id
daily_dd_limit
max_dd_limit
exposure_limit
kill_switch
created_at
updated_at
```

## governance_rules

Zweck:

Speichert Governance-Regeln.

Pflichtfelder:

```text
rule_id
rule_name
rule_type
threshold
action
status
created_at
updated_at
```

## system_events

Zweck:

Speichert Ereignisse, die andere Komponenten lesen können.

Pflichtfelder:

```text
event_id
source
type
payload
timestamp
```

Beispiele:

```text
STRATEGY_SCORE_UPDATED
LIFECYCLE_STATUS_CHANGED
PORTFOLIO_ALLOCATION_CHANGED
RISK_ALERT_CREATED
QUANT_SYSTEM_DB_CREATED
```

## audit_logs

Zweck:

Speichert Änderungen an Systemobjekten.

Pflichtfelder:

```text
change_id
object_type
object_id
change
timestamp
user
```

## schema_migrations

Zweck:

Versioniert Datenbankschemaänderungen.

Pflichtfelder:

```text
migration_id
schema_version
applied_at
description
```

---

# 2. TRADE_HISTORY.DB

## Zweck

`Trade_History.db` speichert strukturierte Trade-Historien.

Sie ist die zentrale Quelle für Backtest-, Demo- und Live-Trades.

## Speichert

- Backtest Trades
- Demo Trades
- Live Trades
- Executions
- PnL
- Kommissionen
- Swap
- Slippage
- Order-Referenzen
- Account-Referenzen
- Strategy-Referenzen

## Speichert NICHT

- Roh-CSV-Dateien
- unbereinigte Broker-Exporte
- große Reports
- Screenshots

## Empfohlene Tabellen v1

```text
Trade_History.db
│
├── trades
├── executions
├── trade_import_runs
├── trade_quality_checks
└── schema_migrations
```

## trades Pflichtfelder

```text
trade_id
strategy_id
account_id
symbol
direction
entry_time
exit_time
entry_price
exit_price
volume
pnl
commission
swap
source
created_at
```

## executions Pflichtfelder

```text
execution_id
trade_id
order_id
symbol
side
price
volume
timestamp
broker
account_id
```

---

# 3. MARKET_DATA.DB

## Zweck

`Market_Data.db` speichert standardisierte Marktdaten.

## Speichert

- OHLC
- Volumen
- Indikatoren
- Regimes
- Market Statistics
- Symbol-Metadaten
- Timeframe-Informationen

## Speichert NICHT

- große Raw Tick Files
- Roh-Downloads
- unstrukturierte CSV-Sammlungen

## Empfohlene Tabellen v1

```text
Market_Data.db
│
├── ohlc
├── indicators
├── regimes
├── market_statistics
├── symbols
└── schema_migrations
```

## ohlc Pflichtfelder

```text
symbol
timeframe
timestamp
open
high
low
close
volume
source
created_at
```

## regimes Pflichtfelder

```text
symbol
timeframe
timestamp
regime_type
regime_value
confidence
created_at
```

---

# 4. MONITORING.DB

## Zweck

`Monitoring.db` speichert aktuelle und historische Health-Zustände.

## Speichert

- Pipeline Health
- Database Health
- API Health
- System Health
- Account Health
- Deployment Health
- Alerts
- Heartbeats

## Speichert NICHT

- vollständige Logs
- Rohdaten
- große Performance-Datensätze

## Empfohlene Tabellen v1

```text
Monitoring.db
│
├── pipeline_health
├── database_health
├── api_health
├── system_health
├── alerts
├── heartbeats
└── schema_migrations
```

## pipeline_health Pflichtfelder

```text
pipeline_id
status
last_run
last_success
last_error
runtime_seconds
rows_processed
updated_at
```

## alerts Pflichtfelder

```text
alert_id
alert_level
source
message
status
created_at
resolved_at
```

---

# 5. AUDIT.DB

## Zweck

`Audit.db` speichert ausführliche Nachvollziehbarkeit.

## Speichert

- Systemänderungen
- Regeländerungen
- Deployment-Änderungen
- Portfolio-Änderungen
- Konfigurationsänderungen
- manuelle Eingriffe
- Freigaben

## Empfohlene Tabellen v1

```text
Audit.db
│
├── system_changes
├── rule_changes
├── portfolio_changes
├── deployment_changes
├── configuration_changes
├── decision_logs
└── schema_migrations
```

---

# DATABASE RESPONSIBILITY MATRIX

```text
QUANT_SYSTEM.db
= Systemzustand und Control Plane

Trade_History.db
= Trades und Executions

Market_Data.db
= OHLC, Indicators, Regimes

Monitoring.db
= aktueller Systemzustand und Alerts

Audit.db
= Nachvollziehbarkeit und Änderungen
```

---

# DATA PLACEMENT RULES

## Rule 001

Große Rohdateien gehören in Storage.

## Rule 002

Strukturierte Referenzen gehören in Datenbanken.

## Rule 003

Strategie-, Portfolio-, Account- und Deployment-Status gehört in `QUANT_SYSTEM.db`.

## Rule 004

Trades gehören in `Trade_History.db`.

## Rule 005

OHLC, Indikatoren und Regimes gehören in `Market_Data.db`.

## Rule 006

Health Checks und Alerts gehören in `Monitoring.db`.

## Rule 007

Änderungshistorie gehört in `Audit.db`.

## Rule 008

Keine sensiblen Zugangsdaten in Datenbanken speichern.

Verboten:

```text
API Keys
Passwörter
Broker Login Passwörter
Tokens
```

Erlaubt:

```text
account_id
broker_name
environment
status
```

---

# NAMING STANDARD

## Datenbanknamen

Schema:

```text
<Domain>.db
```

Beispiele:

```text
QUANT_SYSTEM.db
Trade_History.db
Market_Data.db
Monitoring.db
Audit.db
```

## Tabellennamen

Tabellennamen sind:

```text
lowercase
plural
snake_case
```

Beispiele:

```text
strategies
portfolio_members
system_events
audit_logs
```

Nicht erlaubt:

```text
StrategyTable
tblStrategies
data1
test_table
```

## Spaltennamen

Spaltennamen sind:

```text
lowercase
snake_case
```

Beispiele:

```text
strategy_id
created_at
updated_at
account_type
```

---

# ID STANDARD

IDs müssen eindeutig und lesbar sein.

Beispiele:

```text
EA_145
PF_TREND_01
FTMO_01
DEP_001
G014
EVT_20260615_001
```

Keine rein zufälligen Namen für operative Objekte.

---

# TIMESTAMP STANDARD

Alle Zeitfelder nutzen ISO-Format.

Beispiel:

```text
2026-06-15T10:30:00Z
```

Pflichtfelder für operative Tabellen:

```text
created_at
updated_at
```

Events nutzen:

```text
timestamp
```

---

# VERSIONING STANDARD

Schemaänderungen müssen versioniert werden.

Pflichttabelle:

```text
schema_migrations
```

Jede Migration braucht:

```text
migration_id
schema_version
applied_at
description
```

Beispiele:

```text
001_initial_quant_system_schema
002_add_strategy_tags
003_add_deployment_environment
```

---

# RELATIONSHIP STANDARD

Foreign Keys sind Pflicht, wenn Tabellen direkt zusammenhängen.

Beispiele:

```text
portfolio_members.strategy_id → strategies.strategy_id

portfolio_members.portfolio_id → portfolios.portfolio_id

deployments.strategy_id → strategies.strategy_id

deployments.account_id → accounts.account_id

risk_limits.account_id → accounts.account_id
```

---

# INSERT RULES

## Rule 001

Neue operative Objekte werden nicht direkt manuell in SQLite geschrieben, außer in der Testphase.

## Rule 002

Später sollen Registry Manager oder validierte Scripts Inserts durchführen.

Beispiele:

```text
register_strategy.py
register_account.py
register_portfolio.py
register_deployment.py
```

## Rule 003

Jeder produktive Insert muss validiert werden.

## Rule 004

Jeder kritische Insert muss ein Event oder Audit erzeugen.

---

# UPDATE RULES

## Rule 001

Statusänderungen müssen nachvollziehbar sein.

Beispiele:

```text
active → paused
HOT → COOLING
running → stopped
```

## Rule 002

Kritische Updates müssen in `audit_logs` oder `Audit.db` landen.

## Rule 003

Scores, Lifecycle und Deployment-Status dürfen später nur durch definierte Engines oder Registry Manager geändert werden.

---

# DELETE RULES

## Rule 001

Produktive Daten werden nicht gelöscht, sondern deaktiviert.

Beispiele:

```text
status = inactive
status = retired
status = deprecated
```

## Rule 002

Hard Deletes sind nur erlaubt für:

```text
Testdaten
Fehlerhafte Seed-Daten
lokale Entwicklung
```

## Rule 003

Hard Deletes in Production benötigen Audit-Eintrag.

---

# BACKUP RULES

Alle produktiven Datenbanken müssen gesichert werden.

Pflicht:

```text
QUANT_SYSTEM.db
Trade_History.db
Market_Data.db
Monitoring.db
Audit.db
```

Empfohlen:

```text
daily backup
weekly archive
monthly cold backup
```

---

# VALIDATION RULES

Jede Datenbank muss prüfbar sein.

Minimum Validation:

```text
Database exists
Database readable
Database writable
Required tables exist
Required columns exist
Foreign keys enabled
Schema version known
```

---

# SECURITY RULES

## Rule 001

Keine Passwörter in Datenbanken.

## Rule 002

Keine API Keys in Datenbanken.

## Rule 003

Keine Broker-Zugangsdaten in Datenbanken.

## Rule 004

Zugangsdaten nur über ENV-Variablen oder sichere Secret Stores.

---

# DEVELOPMENT VS PRODUCTION

## Development

Erlaubt:

```text
Seed Data
Test Accounts
Test Strategies
Hard Deletes
Schema Experiments
```

## Production

Erlaubt nur:

```text
validierte Inserts
auditierte Updates
Backups vor Migrationen
keine manuellen Änderungen ohne Dokumentation
```

---

# MINIMUM DATABASE V1

Für die erste funktionsfähige Version reicht:

```text
QUANT_SYSTEM.db
```

mit:

```text
strategies
portfolios
portfolio_members
accounts
deployments
risk_limits
governance_rules
system_events
audit_logs
schema_migrations
```

Danach:

```text
Trade_History.db
```

Dann:

```text
Market_Data.db
```

Später:

```text
Monitoring.db
Audit.db
```

---

# PRINCIPLE

Eine Datenbank ist kein Dateiablageort.

Eine Datenbank speichert strukturierte Informationen.

Jede Datenbank hat genau eine Hauptverantwortung.

QUANT_SYSTEM.db ist die zentrale Control Plane.

Trade_History.db speichert Trades.

Market_Data.db speichert Marktdaten.

Monitoring.db speichert Systemzustände.

Audit.db speichert Nachvollziehbarkeit.
