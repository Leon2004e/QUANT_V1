INFRASTRUCTURE LAYER

Wenn die Control Plane das Gehirn ist:

```
QUANT_SYSTEM.db
```

dann ist die Infrastructure:

```
Nervensystem
Stromversorgung
Serverraum
Netzwerk
```

alles worauf QUANT OS läuft.

---

# Struktur

```
INFRASTRUCTURE
│
├── Storage
├── Databases
├── APIs
├── Scheduler
├── Logging
├── Monitoring
├── Backup
├── VPS Infrastructure
└── Automation
```

---

# STORAGE

Speichert Dateien.

```
Storage
│
├── Raw Data
├── Pipeline Data
├── Baseline Data
├── Research Data
├── Production Data
├── Monitoring Data
├── Reports
├── Backups
└── Documentation
```

Beispiel:

```
Data_Center
│
└── Data
    │
    ├── 0_Raw
    ├── 1_Pipeline
    ├── 2_Baseline
    ├── 3_Research
    ├── 4_Production
    ├── 5_Monitoring
    └── 6_System
```

---

# DATABASES

Speichert strukturierte Daten.

```
Databases
│
├── QUANT_SYSTEM.db
├── Trade_History.db
├── Market_Data.db
├── Monitoring.db
└── Audit.db
```

### QUANT_SYSTEM.db

Control Plane

```
Strategies
Portfolios
Accounts
Deployments
Rules
Events
```

### Trade_History.db

```
Alle Trades

Backtest
Demo
Live
```

### Market_Data.db

```
OHLC
Indicators
Regimes
Market Statistics
```

---

# APIs

Verbindungen zu externen Systemen.

```
APIs
│
├── MT5 API
├── Broker APIs
├── Dashboard API
├── Internal APIs
└── AI APIs
```

Beispiel:

```
MT5
↓
Trade Logger

Broker
↓
Execution Center

Dashboard
↓
Frontend
```

---

# SCHEDULER

Automatisiert Aufgaben.

```
Scheduler
│
├── Import Jobs
├── Score Jobs
├── Ranking Jobs
├── Lifecycle Jobs
├── Allocation Jobs
├── Report Jobs
└── Backup Jobs
```

Beispiel:

```
08:00 Import Trades

08:05 Update Scores

08:10 Update Lifecycle

08:15 Update Portfolio

08:20 Update Dashboard
```

---

# LOGGING

Alles wird protokolliert.

```
Logging
│
├── Data Logs
├── Strategy Logs
├── Portfolio Logs
├── Execution Logs
├── Risk Logs
├── Governance Logs
└── Error Logs
```

Beispiel:

```
2026-06-11

Strategy Score Updated

EA_145

84 → 91
```

---

# MONITORING

Überwacht die Gesundheit.

```
Monitoring
│
├── System Health
├── Data Health
├── Database Health
├── Broker Health
├── VPS Health
├── Dashboard Health
└── Center Health
```

Beispiel:

```
MT5 Connected

YES

Last Trade Import

08:03

Status

OK
```

---

# BACKUP

Sicherung.

```
Backup
│
├── Database Backup
├── Strategy Backup
├── Portfolio Backup
├── Config Backup
├── Dashboard Backup
└── Full System Backup
```

---

# VPS INFRASTRUCTURE

Hier läuft das Live-System.

```
VPS Infrastructure
│
├── VPS 01
├── VPS 02
├── VPS 03
├── VPS 04
└── VPS Monitoring
```

Beispiel:

```
VPS 01

FTMO Accounts

VPS 02

Demo Accounts

VPS 03

Research

VPS 04

Production
```

---

# AUTOMATION

Das ist später dein größter Hebel.

```
Automation
│
├── Auto Import
├── Auto Scoring
├── Auto Ranking
├── Auto Lifecycle
├── Auto Allocation
├── Auto Monitoring
├── Auto Reporting
└── Auto Alerts
```

Beispiel:

```
Neue Trades
↓
Score Update
↓
Lifecycle Update
↓
Portfolio Update
↓
Dashboard Update
↓
Alert falls nötig
```