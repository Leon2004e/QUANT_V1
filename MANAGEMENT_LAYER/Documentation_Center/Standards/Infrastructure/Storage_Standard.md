# STORAGE STANDARD

Layer: Infrastructure

Status: Active

Version: 1.0

---

# PURPOSE

Storage definiert die Speicherung aller dateibasierten Daten innerhalb von QUANT OS.

Storage ist verantwortlich für:

* Rohdaten
* Verarbeitete Daten
* Referenzdaten
* Research Daten
* Production Daten
* Monitoring Daten
* Systemdaten

Storage speichert Dateien.

Storage enthält keine Geschäftslogik.

---

# STORAGE STRUCTURE

```text
Data_Center/
└── Data/
    ├── 0_Raw/
    ├── 1_Pipeline/
    ├── 2_Baseline/
    ├── 3_Research/
    ├── 4_Production/
    ├── 5_Monitoring/
    └── 6_System/
```

---

# 0_RAW

Zweck:

Speicherung unveränderter Originaldaten.

Beispiele:

* MT5 Exports
* Broker Exports
* Original CSV Dateien
* Original Market Data
* Original Trade Data

Regeln:

* Read Only
* Keine Bearbeitung
* Keine Normalisierung
* Keine Überschreibung

Erlaubt:

* Lesen
* Archivieren
* Kopieren

Nicht erlaubt:

* Modifizieren
* Überschreiben

---

# 1_PIPELINE

Zweck:

Verarbeitungsebene.

Beispiele:

* Bereinigte Daten
* Normalisierte Daten
* Zusammengeführte Daten
* Transformierte Daten

Regeln:

* Darf neu erzeugt werden
* Darf überschrieben werden
* Darf gelöscht werden

---

# 2_BASELINE

Zweck:

Standardisierte Referenzdaten.

Beispiele:

* Baseline Trades
* Baseline Equity Curves
* Baseline Strategy Metrics
* Baseline Market Data

Regeln:

* Referenzebene für Analysen
* Nur kontrollierte Updates

---

# 3_RESEARCH

Zweck:

Experimente und Analysen.

Beispiele:

* Regime Tests
* Feature Tests
* Correlation Studies
* Strategy Research

Regeln:

* Sandbox Bereich
* Keine direkte Nutzung in Production

---

# 4_PRODUCTION

Zweck:

Produktive Daten.

Beispiele:

* Aktive Strategien
* Aktive Portfolios
* Freigegebene Scores
* Produktionskonfigurationen

Regeln:

* Nur freigegebene Daten
* Keine Experimente
* Änderungen müssen nachvollziehbar sein

---

# 5_MONITORING

Zweck:

Überwachung des Systems.

Beispiele:

* Health Checks
* Alerts
* Status Reports
* Monitoring Snapshots

Regeln:

* Automatisch erzeugt
* Keine manuelle Bearbeitung

---

# 6_SYSTEM

Zweck:

Technische Systemdaten.

Beispiele:

* Config Dateien
* Schemas
* Registry Dateien
* Metadaten

Regeln:

* Keine Markt- oder Trade-Daten
* Nur Systeminformationen

---

# STORAGE FLOW

Jede Datei folgt grundsätzlich folgendem Weg:

```text
0_Raw
↓
1_Pipeline
↓
2_Baseline
↓
3_Research
oder
4_Production
↓
5_Monitoring
↓
Backup
```

---

# FILE NAMING STANDARD

Schema:

```text
<domain>_<asset>_<type>_<version>
```

Beispiele:

```text
trades_gbpjpy_baseline_v1.csv

portfolio_trend_weights_v3.csv

strategy_ea145_score_v2.csv

monitoring_system_health_v1.csv
```

Nicht erlaubt:

```text
final.csv
new.csv
latest.csv
test.csv
```

---

# VERSIONING RULE

Versionierung ist verpflichtend für:

* Production Dateien
* System Dateien
* Konfigurationen
* Portfolio Dateien
* Strategie Dateien

Beispiele:

```text
risk_config_v1.json

risk_config_v2.json

risk_config_v3.json
```

---

# DELETION RULES

0_Raw

* Niemals löschen

1_Pipeline

* Darf neu erzeugt werden

2_Baseline

* Nur kontrolliert ersetzen

3_Research

* Darf archiviert werden

4_Production

* Nur mit Freigabe ersetzen

5_Monitoring

* Automatisch verwaltet

6_System

* Nur kontrollierte Änderungen

---

# PRINCIPLE

Storage ist die einzige Quelle für dateibasierte Daten innerhalb von QUANT OS.

Alle Dateien müssen einer Storage-Kategorie zugeordnet sein.

Keine Datei darf außerhalb des definierten Storage Systems dauerhaft gespeichert werden.
