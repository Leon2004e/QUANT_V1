# CONTROL PLANE

Wenn:

```
Frontend = Anzeige
Backend = Verarbeitung
Management = Verwaltung
```

dann ist:

```
Control Plane = Gehirn
```

---

# Aufgabe

Die Control Plane weiß:

```
Welche Strategien existieren?
Welche Portfolios existieren?
Welche Accounts existieren?
Welche Deployments laufen?
Welche Regeln gelten?
```

---

# Struktur

```
CONTROL PLANE
│
└── QUANT_SYSTEM.db
```

---

# Was speichert QUANT_SYSTEM.db?

Nicht:

```
Tickdaten
OHLC Daten
Backtests
Große CSV Dateien
```

sondern:

```
Metadaten
Status
Konfigurationen
Referenzen
```

---

# Strategy Registry

```
strategies
│
├── strategy_id
├── strategy_name
├── version
├── status
├── lifecycle
├── score
└── created_at
```

Beispiel:

```
EA_145

Status: Active
Lifecycle: HOT
Score: 91
```

---

# Portfolio Registry

```
portfolios
│
├── portfolio_id
├── portfolio_name
├── status
└── created_at
```

---

# Portfolio Members

```
portfolio_members
│
├── portfolio_id
├── strategy_id
└── weight
```

Beispiel:

```
Trend Portfolio

EA_145 = 12%
EA_221 = 8%
EA_344 = 5%
```

---

# Account Registry

```
accounts
│
├── account_id
├── broker
├── account_type
├── balance
└── status
```

Beispiel:

```
FTMO_01

200k
LIVE
```

---

# Deployments

```
deployments
│
├── deployment_id
├── strategy_id
├── account_id
├── version
└── status
```

Beispiel:

```
EA_145

Account:
FTMO_01

Status:
Running
```

---

# Risk Registry

```
risk_limits
│
├── account_id
├── daily_dd_limit
├── max_dd_limit
├── exposure_limit
└── kill_switch
```

---

# Governance Registry

```
governance_rules
│
├── rule_id
├── rule_name
├── rule_type
├── threshold
└── action
```

Beispiel:

```
G014

90 Day Score < 55

Action:
Cooling
```

---

# Events

Sehr wichtig.

```
system_events
│
├── event_id
├── source
├── type
├── payload
└── timestamp
```

Beispiel:

```
STRATEGY_SCORE_UPDATED

EA_145

84 → 91
```

---

# Audit Logs

```
audit_logs
│
├── change_id
├── object_type
├── object_id
├── change
└── timestamp
```

---

# Warum ist die Control Plane wichtig?

Weil dann jedes Center nicht mehr direkt miteinander reden muss.

Statt:

```
Strategy Center
↓
Portfolio Center
↓
Risk Center
↓
Operations Center
```

machen alle:

```
Center
↓
QUANT_SYSTEM.db
↓
Center
```

---

# Beispiel

```
Strategy Center
```

schreibt:

```
EA_145

Score = 91
Lifecycle = HOT
```

in:

```
QUANT_SYSTEM.db
```

Dann liest:

```
Portfolio Center
```

automatisch:

```
HOT
Score = 91
```

und erhöht das Gewicht.

---

# Komplettes Bild

```
FRONTEND
     ▲
     │
     │
CONTROL PLANE
     │
     ▼

BACKEND
│
├── Data Center
├── Strategy Center
├── Portfolio Center
├── Execution Center
├── Operations Center
├── Intelligence Center
├── Risk Center
└── Governance Center

MANAGEMENT
│
├── Registries
├── Catalogs
├── Configs
└── Documentation
```

Das ist der eigentliche Kern eines Operating Systems:

```
Alles läuft über die Control Plane.
```

Der nächste Layer wäre dann:

```
INFRASTRUCTURE LAYER
```

also wo Daten, Datenbanken, APIs, Scheduler, VPS, Monitoring und Automatisierung tatsächlich laufen.