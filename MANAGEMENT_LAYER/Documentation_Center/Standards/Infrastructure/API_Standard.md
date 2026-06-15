# API STANDARD

Layer: Infrastructure  
Status: Active  
Version: 1.0  
Owner: Leon Everts  
System: QUANT OS

---

# PURPOSE

Der API Standard definiert, wie QUANT OS mit externen und internen Systemen kommuniziert.

API bedeutet in QUANT OS nicht nur Web-API.

API bedeutet jede klare Schnittstelle zwischen Komponenten.

Beispiele:

- MT5 zu Trade Logger
- Broker zu Execution Center
- Data Center zu Strategy Center
- Strategy Center zu Control Plane
- Control Plane zu Frontend
- Scripts zu Datenbanken
- AI Services zu Analytics

---

# CORE PRINCIPLE

```text
Keine Schnittstelle ohne definierte Inputs.

Keine Schnittstelle ohne definierte Outputs.

Keine Schnittstelle ohne Error Handling.

Keine Schnittstelle ohne Versionierung.
```

---

# API TYPES

QUANT OS unterscheidet folgende API-Typen:

```text
External APIs
Internal APIs
Database Interfaces
Dashboard APIs
AI APIs
File Interfaces
```

---

# 1. EXTERNAL APIS

Externe APIs verbinden QUANT OS mit Systemen außerhalb des Projekts.

Beispiele:

```text
MT5 API
Broker API
Economic Calendar API
Market Data API
AI API
```

## Aufgaben

- Daten abrufen
- Orders senden
- Accountinformationen abrufen
- externe Signale lesen
- externe Services verbinden

## Regeln

- keine Zugangsdaten im Code
- Zugangsdaten nur über ENV-Variablen
- Timeouts definieren
- Retry-Logik definieren
- Fehler strukturiert zurückgeben
- API-Ausfälle loggen

---

# 2. INTERNAL APIS

Interne APIs verbinden Layer und Center innerhalb von QUANT OS.

Beispiele:

```text
Data Center → Strategy Center
Strategy Center → Control Plane
Portfolio Center → Control Plane
Control Plane → Frontend
Management → Control Plane
```

## Aufgaben

- strukturierte Daten übergeben
- Status abfragen
- Events schreiben
- Outputs lesen
- Registries aktualisieren

---

# 3. DATABASE INTERFACES

Datenbankzugriffe gelten ebenfalls als Schnittstellen.

Beispiele:

```text
read_strategies()
insert_strategy()
update_strategy_score()
read_portfolio_members()
insert_system_event()
write_audit_log()
```

## Regeln

- keine SQL-Logik wild im gesamten Code verteilen
- zentrale DB-Funktionen nutzen
- Eingaben validieren
- Schreibzugriffe loggen
- kritische Änderungen auditieren

---

# 4. DASHBOARD APIS

Dashboard APIs liefern Daten an das Frontend.

Beispiele:

```text
get_code_registry_table()
get_quant_system_status()
get_database_health()
get_pipeline_health()
get_strategy_ranking()
```

## Regeln

- Frontend berechnet nicht schwer
- Frontend liest Outputs
- Backend und Control Plane liefern Daten
- Dashboard APIs liefern saubere, kleine Datenpakete

---

# 5. AI APIS

AI APIs verbinden QUANT OS mit AI-Services.

Beispiele:

```text
strategy_analysis_request()
regime_summary_request()
portfolio_diagnostics_request()
code_review_request()
```

## Regeln

- keine sensiblen Brokerdaten senden
- keine Passwörter senden
- Input klar begrenzen
- Output speichern, wenn er operative Bedeutung hat
- AI-Entscheidungen nicht ungeprüft produktiv nutzen

---

# 6. FILE INTERFACES

Auch Dateien sind Schnittstellen.

Beispiele:

```text
Pipeline schreibt baseline_trades.csv
Strategy Center liest baseline_trades.csv
```

## Regeln

- Dateischema definieren
- Dateiname standardisieren
- Versionierung nutzen
- keine zufälligen Spaltennamen
- Output-Metadaten schreiben

---

# API NAMING STANDARD

Funktionsnamen müssen eindeutig, lesbar und handlungsbezogen sein.

Schema:

```text
<action>_<object>
```

Beispiele:

```text
get_strategy_score()
update_strategy_lifecycle()
insert_system_event()
read_account_status()
write_portfolio_allocation()
validate_trade_data()
```

Nicht erlaubt:

```text
do_stuff()
process()
run()
test()
data()
main_logic()
```

---

# ACTION VERBS

Erlaubte Standard-Verben:

```text
get
read
load
write
insert
update
delete
validate
create
export
import
sync
check
calculate
generate
```

Beispiele:

```text
read_strategies()
insert_account()
update_deployment_status()
validate_database_schema()
calculate_strategy_score()
```

---

# INPUT STANDARD

Jede API-Funktion braucht definierte Inputs.

Pflicht:

```text
required_inputs
optional_inputs
input_types
validation_rules
```

Beispiel:

```text
strategy_id: str
score: float
timestamp: str
source: str
```

## Input Regeln

- Pflichtfelder prüfen
- Datentypen prüfen
- Wertebereiche prüfen
- leere Strings vermeiden
- None nur erlaubt, wenn dokumentiert

---

# OUTPUT STANDARD

Jede API gibt ein standardisiertes Ergebnis zurück.

Standardformat:

```json
{
  "success": true,
  "message": "Action completed",
  "data": {},
  "error": null,
  "timestamp": "2026-06-15T10:30:00Z"
}
```

Bei Fehler:

```json
{
  "success": false,
  "message": "Database write failed",
  "data": null,
  "error": {
    "type": "DatabaseError",
    "code": "DB_WRITE_FAILED",
    "details": "SQLite database locked"
  },
  "timestamp": "2026-06-15T10:30:00Z"
}
```

---

# ERROR CODE STANDARD

Fehlercodes sollen maschinenlesbar sein.

Beispiele:

```text
DB_CONNECTION_FAILED
DB_WRITE_FAILED
DB_READ_FAILED
API_TIMEOUT
API_AUTH_FAILED
API_RESPONSE_INVALID
FILE_NOT_FOUND
SCHEMA_INVALID
VALIDATION_FAILED
UNKNOWN_ERROR
```

---

# API VERSIONING

APIs müssen versionierbar sein.

Ordnerstruktur:

```text
api/
├── v1/
└── v2/
```

oder Funktionsschema:

```text
get_strategy_score_v1()
get_strategy_score_v2()
```

Versionierung ist Pflicht bei Breaking Changes.

---

# TIMEOUT STANDARD

Externe API Calls brauchen Timeouts.

Empfehlung:

```text
MT5 API: 10-30 Sekunden
Broker API: 10-30 Sekunden
Market Data API: 10-60 Sekunden
AI API: 30-180 Sekunden
```

---

# RETRY STANDARD

Für externe APIs:

```text
max_retries: 3
retry_delay_seconds: 2
exponential_backoff: optional
```

Nicht blind unendlich wiederholen.

---

# SECURITY RULES

## Rule 001

Keine Zugangsdaten im Code.

## Rule 002

API Keys nur über ENV-Variablen oder Secret Store.

## Rule 003

Keine Passwörter in Logs.

## Rule 004

Fehlerausgaben dürfen keine sensiblen Informationen enthalten.

## Rule 005

Nur notwendige Daten an externe APIs senden.

---

# API DOCUMENTATION

Jede API muss dokumentieren:

```text
purpose
inputs
outputs
errors
owner
version
status
dependencies
security_notes
```

---

# API REGISTRY

Jede produktive API oder Schnittstelle muss in der Code Registry registriert werden.

Minimum Registry Fields:

```text
api_id
api_name
owner
status
layer
center
purpose
inputs
outputs
version
dependencies
```

---

# API TESTING

Jede API braucht mindestens:

```text
success case
missing input case
invalid input case
error case
```

---

# API LOGGING

Jede API muss loggen:

```text
request started
request completed
request failed
duration
error code
```

Keine sensiblen Payloads loggen.

---

# MINIMUM API V1

Für die erste QUANT OS Version reichen:

```text
Database Interfaces
File Interfaces
MT5 API Interface
Dashboard Read Interfaces
```

Noch nicht nötig:

```text
vollständige Web API
Cloud API
Multi-user API
```

---

# PRINCIPLE

APIs sind Verträge zwischen Systemteilen.

Wenn Inputs und Outputs nicht klar sind, ist das System nicht skalierbar.

Jede Schnittstelle muss lesbar, testbar und versionierbar sein.
