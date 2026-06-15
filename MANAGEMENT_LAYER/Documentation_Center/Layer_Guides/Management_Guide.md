# MANAGEMENT LAYER

Während:

```
Frontend
= Bedienung

Backend
= Verarbeitung
```

ist

```
Management
= Verwaltung
```

---

# Grundstruktur

```
MANAGEMENT
│
├── Registry
├── Catalog
├── Configuration
├── Documentation
├── Versioning
└── Audit
```

---

# 1. Code Registry

Verwaltet alle Software-Komponenten.

```
Code Registry
│
├── Scripts
├── Apps
├── Engines
├── APIs
├── Widgets
├── Building Blocks
├── Utilities
└── Versions
```

Beispiel:

```
strategy_score_engine.py

Owner: Leon
Version: 2.3
Status: Active
Center: Strategy Center
```

---

# 2. Asset Registry

Verwaltet alle Trading-Assets.

```
Asset Registry
│
├── Strategies
├── Portfolios
├── Accounts
├── Brokers
├── Symbols
├── Datasets
└── Models
```

Beispiel:

```
EA_145

Status: HOT
Portfolio: Trend
Version: 4
```

---

# 3. Account Registry

Verwaltet alle Konten.

```
Account Registry
│
├── Demo Accounts
├── Live Accounts
├── Prop Accounts
└── Broker Accounts
```

Beispiel:

```
FTMO_01
Balance: 200k
Status: Active
```

---

# 4. Broker Registry

```
Broker Registry
│
├── FTMO
├── IC Markets
├── Dukascopy
├── Darwinex
└── Future Brokers
```

---

# 5. Deployment Registry

Verwaltet alle Deployments.

```
Deployment Registry
│
├── Demo Deployments
├── Live Deployments
├── VPS Deployments
└── Rollback History
```

Beispiel:

```
EA_145

Demo
→ Live

Date: 2026-06-15
```

---

# 6. Data Catalog

Verwaltet Datenquellen.

```
Data Catalog
│
├── Market Data
├── Trade Data
├── Research Data
├── Production Data
└── Monitoring Data
```

---

# 7. Configuration Manager

Verwaltet Einstellungen.

```
Configuration Manager
│
├── Risk Configs
├── Portfolio Configs
├── Strategy Configs
├── Dashboard Configs
└── Automation Configs
```

---

# 8. Version Manager

Verwaltet Versionen.

```
Version Manager
│
├── Strategy Versions
├── Code Versions
├── Portfolio Versions
└── Deployment Versions
```

---

# 9. Documentation Center

Verwaltet Wissen.

```
Documentation Center
│
├── Architecture
├── Workflows
├── Standards
├── Playbooks
├── Checklists
└── Roadmaps
```

---

# 10. Audit Management

Verwaltet Nachvollziehbarkeit.

```
Audit Management
│
├── System Changes
├── Rule Changes
├── Portfolio Changes
├── Deployments
└── Decision Logs
```

---

# Komplettes Management Layer

```
MANAGEMENT LAYER
│
├── Code Registry
│
├── Asset Registry
│
├── Account Registry
│
├── Broker Registry
│
├── Deployment Registry
│
├── Data Catalog
│
├── Configuration Manager
│
├── Version Manager
│
├── Documentation Center
│
└── Audit Management
```

### Aufgabe des Management Layers

Wenn das Backend fragt:

```
Welche Strategie?
Welche Version?
Welches Portfolio?
Welcher Account?
Welcher Broker?
Welche Konfiguration?
```

dann liefert das Management Layer die Antworten.

Kurz:

```
Frontend
= Anzeigen

Backend
= Arbeiten

Management
= Verwalten
```

Der nächste große Layer wäre dann:

```
CONTROL PLANE
```

also die zentrale QUANT_SYSTEM.db und wie alle Layer miteinander verbunden werden.