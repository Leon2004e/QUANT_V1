# MONITORING STANDARD

Layer: Infrastructure  
Status: Active  
Version: 1.0  
Owner: Leon Everts  
System: QUANT OS

---

# PURPOSE

Der Monitoring Standard definiert, wie QUANT OS den aktuellen Zustand von Systemen, Pipelines, Datenbanken, APIs, Accounts, Deployments, Strategien, Portfolios und Risiken überwacht.

Monitoring beantwortet:

- Läuft das System gerade?
- Ist eine Pipeline gesund?
- Ist eine Datenbank erreichbar?
- Ist eine API verbunden?
- Gibt es Alerts?
- Sind Accounts im Limit?
- Sind Deployments aktiv?
- Gibt es Systemprobleme?

---

# CORE PRINCIPLE

```text
Logging = Was ist passiert?

Monitoring = Wie ist der aktuelle Zustand?
```

Monitoring zeigt Status.

Logging zeigt Historie.

---

# MONITORING AREAS

QUANT OS überwacht:

```text
System Health
Pipeline Health
Database Health
API Health
Account Health
Deployment Health
Strategy Health
Portfolio Health
Risk Health
Data Health
Alerts
Heartbeats
```

---

# STATUS STANDARD

Erlaubte Statuswerte:

```text
OK
WARN
ERROR
CRITICAL
UNKNOWN
```

## OK

System ist gesund.

## WARN

Problem vorhanden, aber System kann weiterlaufen.

## ERROR

Fehler vorhanden, Eingriff erforderlich.

## CRITICAL

Kritischer Zustand, Risiko für System oder Kapital.

## UNKNOWN

Status kann nicht bestimmt werden.

---

# ALERT LEVELS

Erlaubte Alert Levels:

```text
INFO
WARN
ERROR
CRITICAL
```

---

# 1. SYSTEM HEALTH

Überwacht:

```text
CPU
RAM
Disk
Network
Runtime Environment
Python Environment
```

Metriken:

```text
cpu_percent
ram_percent
disk_percent
network_status
python_version
status
updated_at
```

---

# 2. PIPELINE HEALTH

Überwacht:

```text
Trade Logger
Market Data Import
Trade Normalizer
Baseline Builder
Data Validation
```

Metriken:

```text
pipeline_id
status
last_run
last_success
last_error
runtime_seconds
rows_processed
output_path
updated_at
```

Beispiel:

```json
{
  "pipeline_id": "trade_logger",
  "status": "OK",
  "last_success": "2026-06-15T10:30:00Z",
  "rows_processed": 1250
}
```

---

# 3. DATABASE HEALTH

Überwacht:

```text
QUANT_SYSTEM.db
Trade_History.db
Market_Data.db
Monitoring.db
Audit.db
```

Metriken:

```text
database_name
exists
readable
writable
size_mb
last_modified
schema_version
status
updated_at
```

---

# 4. API HEALTH

Überwacht:

```text
MT5 API
Broker API
Dashboard API
Internal API
AI API
```

Metriken:

```text
api_name
connected
last_success
last_error
response_time_ms
status
updated_at
```

---

# 5. ACCOUNT HEALTH

Überwacht:

```text
Balance
Equity
Daily DD
Max DD
Exposure
Account Status
Broker Connection
```

Metriken:

```text
account_id
broker
balance
equity
daily_dd
max_dd
exposure
status
updated_at
```

---

# 6. DEPLOYMENT HEALTH

Überwacht:

```text
deployment_id
strategy_id
account_id
version
vps
status
started_at
last_heartbeat
```

Zweck:

Erkennen, ob eine Strategie auf einem Account korrekt läuft.

---

# 7. STRATEGY HEALTH

Überwacht:

```text
strategy_id
lifecycle
score
last_trade
recent_pnl
drawdown
status
```

Wichtig:

Strategy Health kommt erst vollständig, wenn Strategy Center Outputs existieren.

---

# 8. PORTFOLIO HEALTH

Überwacht:

```text
portfolio_id
portfolio_status
drawdown
exposure
active_strategies
allocation_status
last_rebalance
```

Wichtig:

Portfolio Health kommt erst vollständig, wenn Portfolio Center Outputs existieren.

---

# 9. RISK HEALTH

Überwacht:

```text
daily_dd_status
max_dd_status
exposure_status
kill_switch_status
risk_alerts
```

Beispiele:

```text
Daily DD = OK
Max DD = OK
Exposure = WARN
Kill Switch = OFF
```

---

# 10. DATA HEALTH

Überwacht:

```text
missing_data
stale_data
duplicate_data
schema_errors
invalid_timestamps
invalid_symbols
```

Metriken:

```text
dataset_id
status
row_count
missing_count
duplicate_count
last_update
updated_at
```

---

# 11. HEARTBEATS

Heartbeats zeigen, ob Komponenten noch leben.

Beispiel:

```text
trade_logger heartbeat every 60 seconds
database_checker heartbeat every 300 seconds
```

Pflichtfelder:

```text
component_id
status
last_heartbeat
message
```

---

# MONITORING STORAGE

Monitoring-Daten werden gespeichert unter:

```text
Backend/Data_Center/Data/5_Monitoring/
```

Empfohlene Struktur:

```text
5_Monitoring/
│
├── System_Health/
├── Pipeline_Health/
├── Database_Health/
├── API_Health/
├── Account_Health/
├── Deployment_Health/
├── Strategy_Health/
├── Portfolio_Health/
├── Risk_Health/
├── Data_Health/
├── Alerts/
└── Logs/
```

---

# MONITORING FILE FORMAT

Empfohlen:

```text
JSON
SQLite
CSV nur für einfache Reports
```

Beispiele:

```text
database_health.json
pipeline_health.json
api_health.json
alerts.json
```

---

# ALERT STRUCTURE

Jeder Alert muss enthalten:

```text
alert_id
alert_level
source
message
status
created_at
resolved_at
```

Statuswerte:

```text
open
acknowledged
resolved
ignored
```

---

# ALERT EXAMPLES

```text
MT5 connection lost
QUANT_SYSTEM.db unavailable
Pipeline failed
Daily DD limit exceeded
No new trade import for 24h
Disk usage above 90%
```

---

# MONITORING RULES

## Rule 001

Jede produktive Pipeline muss einen Health Status besitzen.

## Rule 002

Jede produktive Datenbank muss Health Checks besitzen.

## Rule 003

Jeder kritische Fehler muss einen Alert erzeugen.

## Rule 004

Monitoring darf keine Rohdaten speichern.

## Rule 005

Monitoring darf keine sensiblen Zugangsdaten speichern.

## Rule 006

Monitoring-Daten müssen maschinenlesbar sein.

## Rule 007

Jede aktive Deployment-Komponente braucht später einen Heartbeat.

## Rule 008

Ein UNKNOWN Status ist besser als ein falscher OK Status.

---

# MONITORING FREQUENCY

Empfohlene Frequenzen:

```text
Database Health: alle 5-15 Minuten
Pipeline Health: nach jedem Lauf
API Health: alle 1-15 Minuten je nach Kritikalität
Account Health: alle 1-5 Minuten im Live-Betrieb
System Health: alle 1-5 Minuten
Risk Health: realtime oder nach jedem Trade
```

---

# MINIMUM MONITORING V1

Für die erste Version von QUANT OS reicht:

```text
Database Health
Pipeline Health
API Health
Alerts
```

Noch nicht zwingend:

```text
Portfolio Health
Strategy Health
Deployment Health
Risk Health
```

Diese kommen später, wenn echte Backend-Outputs existieren.

---

# MONITORING VS LOGGING

```text
Logging:
Trade Logger hat um 10:00 gestartet.
Trade Logger hat um 10:01 1250 Trades importiert.

Monitoring:
Trade Logger Status = OK.
Letzter erfolgreicher Lauf = 10:01.
```

---

# PRINCIPLE

Monitoring sagt, ob das System gerade gesund ist.

Keine produktive Pipeline ohne Health Status.

Keine produktive Datenbank ohne Health Check.

Kein kritischer Fehler ohne Alert.

Monitoring macht QUANT OS kontrollierbar.
