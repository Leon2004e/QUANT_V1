# LOGGING STANDARD

Layer: Infrastructure  
Status: Active  
Version: 1.0  
Owner: Leon Everts  
System: QUANT OS

---

# PURPOSE

Der Logging Standard definiert, wie QUANT OS Ereignisse, Fehler, Warnungen, technische Abläufe und Systemaktionen protokolliert.

Logging beantwortet:

- Was ist passiert?
- Wann ist es passiert?
- Wo ist es passiert?
- Welcher Code war beteiligt?
- Welche Daten waren betroffen?
- War die Aktion erfolgreich?
- Gab es einen Fehler?
- Muss der Fehler untersucht werden?

Logging ist Pflicht für produktive Scripts, Pipelines, Engines, APIs, Datenbankprozesse und Automationen.

---

# CORE PRINCIPLE

```text
Logging = Was ist passiert?

Monitoring = Wie ist der aktuelle Zustand?
```

Logging ist Historie.

Monitoring ist aktueller Zustand.

---

# LOGGING SCOPE

Logging gilt für:

- Pipelines
- Engines
- APIs
- Database Scripts
- Registry Scripts
- Control Plane Scripts
- Backend Center
- Data Imports
- Baseline Builder
- Strategy Scoring
- Portfolio Allocation
- Risk Checks
- Deployments
- Backups
- Validation Scripts

---

# LOG LEVELS

Erlaubte Log Levels:

```text
DEBUG
INFO
OK
WARN
ERROR
CRITICAL
```

---

# LOG LEVEL DEFINITIONS

## DEBUG

Technische Details für Entwicklung und Debugging.

Beispiele:

```text
Parsed 12 columns from CSV
SQL query executed in 0.12 seconds
```

## INFO

Normale Statusmeldung.

Beispiele:

```text
Trade Logger started
Loading input file
Connecting to database
```

## OK

Erfolgreich abgeschlossene Aktion.

Beispiele:

```text
Database created successfully
12500 trades imported
Metadata written
```

## WARN

Problem, aber Prozess kann weiterlaufen.

Beispiele:

```text
Optional config missing
No new trades found
Duplicate row skipped
```

## ERROR

Fehler, Aktion konnte nicht korrekt abgeschlossen werden.

Beispiele:

```text
Input file not found
Database write failed
API connection failed
```

## CRITICAL

Kritischer Fehler, Prozess oder System muss gestoppt werden.

Beispiele:

```text
QUANT_SYSTEM.db unavailable
Risk limit breach detected
Kill switch activated
```

---

# LOG FORMAT

Jeder strukturierte Log-Eintrag muss mindestens enthalten:

```text
timestamp
level
layer
center
component
script_id
message
```

Optional:

```text
run_id
event_type
object_type
object_id
input_path
output_path
rows_processed
duration_seconds
error_code
error_type
details
```

---

# CONSOLE LOG FORMAT

Für einfache Scripts:

```text
[INFO] Starting QUANT_SYSTEM.db creation...
[OK] QUANT_SYSTEM.db created successfully.
[WARN] No new trades found.
[ERROR] SQLite database locked.
```

---

# FILE LOG FORMAT

Für produktive Log-Dateien:

```text
2026-06-15T10:30:22Z | INFO | Backend | Data_Center | Trade_Logger | trade_logger | MT5 connected
```

Erweitert:

```text
2026-06-15T10:30:22Z | OK | Backend | Data_Center | Trade_Logger | trade_logger | rows=1250 | duration=4.2s | Import completed
```

---

# JSON LOG FORMAT

Für maschinenlesbare Logs:

```json
{
  "timestamp": "2026-06-15T10:30:22Z",
  "level": "OK",
  "layer": "Backend",
  "center": "Data_Center",
  "component": "Trade_Logger",
  "script_id": "trade_logger",
  "message": "Import completed",
  "run_id": "RUN_20260615_103022",
  "rows_processed": 1250,
  "duration_seconds": 4.2,
  "error": null
}
```

---

# LOG STORAGE

Logs werden im Monitoring-Bereich gespeichert.

Standardpfad:

```text
Backend/Data_Center/Data/5_Monitoring/Logs/
```

Empfohlene Unterstruktur:

```text
Logs/
│
├── Control_Plane/
│   └── quant_system_db/
│
├── Data_Center/
│   ├── trade_logger/
│   ├── baseline_builder/
│   └── market_data_import/
│
├── Strategy_Center/
│   ├── score_engine/
│   └── lifecycle_engine/
│
├── Portfolio_Center/
│   └── allocation_engine/
│
├── Risk_Center/
│   └── risk_monitor/
│
└── System/
    └── errors/
```

---

# LOG FILE NAMING

Schema:

```text
<component>_<date>.log
```

Beispiele:

```text
trade_logger_2026-06-15.log
baseline_builder_2026-06-15.log
quant_system_db_2026-06-15.log
risk_monitor_2026-06-15.log
```

Für JSON Logs:

```text
<component>_<date>.jsonl
```

Beispiel:

```text
trade_logger_2026-06-15.jsonl
```

---

# RUN ID STANDARD

Jeder produktive Prozesslauf erhält eine `run_id`.

Schema:

```text
RUN_<YYYYMMDD>_<HHMMSS>_<component>
```

Beispiel:

```text
RUN_20260615_103022_trade_logger
```

Zweck:

- alle Logs eines Laufs verbinden
- Fehler nachverfolgen
- Outputs einem Lauf zuordnen
- Debugging vereinfachen

---

# REQUIRED LOG EVENTS

Jeder produktive Code muss mindestens loggen:

```text
START
INPUT_LOADED
PROCESSING_STARTED
PROCESSING_COMPLETED
OUTPUT_WRITTEN
END
```

Bei Fehlern zusätzlich:

```text
ERROR_OCCURRED
PROCESS_FAILED
```

---

# PIPELINE LOGGING REQUIREMENTS

Jede Pipeline muss loggen:

- Startzeit
- Input-Pfad
- Output-Pfad
- Anzahl geladener Zeilen
- Anzahl verarbeiteter Zeilen
- Anzahl geschriebener Zeilen
- Laufzeit
- Fehler
- Status

Beispiel:

```text
[INFO] Loading input: Data/0_Raw/Trades/
[OK] Loaded 12500 rows.
[OK] Written output: Data/1_Pipeline/Trades/
```

---

# DATABASE LOGGING REQUIREMENTS

Jeder Datenbankprozess muss loggen:

- Datenbankpfad
- Verbindung erfolgreich oder fehlgeschlagen
- Migrationen
- Inserts
- Updates
- Fehler
- Tabellenanzahl
- betroffene Zeilen

Beispiel:

```text
[INFO] Connecting to QUANT_SYSTEM.db
[OK] Schema migration applied: 001_initial_quant_system_schema
[ERROR] Database locked
```

---

# API LOGGING REQUIREMENTS

Jede API-Kommunikation muss loggen:

- API Name
- Verbindung
- Request gestartet
- Response erhalten
- Fehler
- Timeout
- Retry

Nicht geloggt werden dürfen:

- Passwörter
- Tokens
- API Keys
- geheime Brokerdaten

---

# ERROR LOGGING REQUIREMENTS

Jeder Fehlerlog muss enthalten:

```text
timestamp
level
component
message
error_type
error_code
details
```

Beispiel:

```text
[ERROR] Database write failed | error_type=OperationalError | code=DB_WRITE_FAILED
```

---

# SENSITIVE DATA RULES

Verboten in Logs:

```text
password
api_key
token
secret
broker_password
private_key
```

Erlaubt:

```text
account_id
broker_name
strategy_id
portfolio_id
deployment_id
```

---

# LOG RETENTION

Empfohlene Aufbewahrung:

```text
Development Logs: 30 Tage
Pipeline Logs: 90 Tage
Production Logs: 180 Tage
Critical Logs: dauerhaft archivieren
Audit-relevante Logs: dauerhaft archivieren
```

---

# LOG ROTATION

Produktive Logs sollen regelmäßig rotiert werden.

Empfohlen:

```text
daily rotation
max file size limit
archive old logs
compress long-term logs
```

---

# LOGGING RULES

## Rule 001

Kein produktiver Code ohne Logging.

## Rule 002

Jeder Pipeline-Start muss geloggt werden.

## Rule 003

Jeder Pipeline-Abschluss muss geloggt werden.

## Rule 004

Jeder Fehler muss geloggt werden.

## Rule 005

Jeder Datenbankfehler muss geloggt werden.

## Rule 006

Jeder API-Fehler muss geloggt werden.

## Rule 007

Keine sensiblen Daten in Logs.

## Rule 008

Logs dürfen nicht manuell verändert werden.

## Rule 009

Kritische Fehler müssen zusätzlich einen Monitoring Alert erzeugen.

## Rule 010

Produktive Logs müssen maschinenlesbar sein oder in maschinenlesbares Format überführt werden können.

---

# MINIMUM LOGGING V1

Für die erste Version von QUANT OS reicht:

```text
Console Logs mit [INFO], [OK], [WARN], [ERROR]
```

plus:

```text
Logdatei pro produktivem Script
```

Später:

```text
JSONL Logs
Monitoring Integration
Alert Integration
Log Dashboard
```

---

# PRINCIPLE

Keine produktive Pipeline ohne Logging.

Keine Engine ohne Error Logging.

Keine API ohne Fehlerprotokollierung.

Keine kritische Aktion ohne Log-Eintrag.

Logging macht QUANT OS debugbar.
