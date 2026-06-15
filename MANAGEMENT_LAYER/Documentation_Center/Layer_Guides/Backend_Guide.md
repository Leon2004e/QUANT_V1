Das **Backend** ist die Produktionsmaschine deines QUANT OS.

Es berechnet, verarbeitet, bewertet, überwacht und erzeugt Outputs für das Frontend.

```
BACKEND LAYER
│
├── Centers
├── Engines
├── Rules
├── Events
└── Outputs
```

## Grundstruktur

```
Center
↓
Engine
↓
Rules
↓
Events
↓
Output
```

## 1. Center

Ein Center ist ein Verantwortungsbereich.

```
Data Center
Strategy Center
Portfolio Center
Execution Center
Operations Center
Intelligence Center
Risk Center
Governance Center
```

## 2. Engine

Eine Engine ist der Code, der arbeitet.

Beispiel:

```
Strategy Center
│
├── Score Engine
├── Ranking Engine
├── Lifecycle Engine
├── Regime Engine
└── Correlation Engine
```

## 3. Rules

Rules sind Regeln, nach denen Engines entscheiden.

Beispiel:

```
Score > 85
AND DD < 5%
→ Status = HOT
```

## 4. Events

Events melden Änderungen im System.

Beispiel:

```
STRATEGY_SCORE_UPDATED
LIFECYCLE_STATUS_CHANGED
PORTFOLIO_ALLOCATION_CHANGED
RISK_ALERT_CREATED
```

## 5. Output

Output ist das Ergebnis eines Centers.

Beispiel:

```
Strategy Center
→ Strategy Score
→ Strategy Rank
→ Lifecycle Status
```

## Komplettbeispiel

```
BACKEND
│
└── Strategy Center
    │
    ├── Score Engine
    ├── Ranking Engine
    ├── Lifecycle Engine
    │
    ├── Promotion Rules
    ├── Demotion Rules
    │
    ├── STRATEGY_SCORE_UPDATED
    └── Output:
        ├── Strategy Score
        ├── Strategy Rank
        └── Lifecycle Status
```

Kurz:

```
Center = Bereich
Engine = Code
Rules = Entscheidungsregeln
Events = Systemnachrichten
Output = Ergebnis
```