Das **Frontend** ist die Bedienoberfläche deines QUANT OS.

Es arbeitet nicht selbst schwer im Hintergrund. Es zeigt, steuert und überwacht die Outputs aus Backend, Management, Control Plane und Infrastructure.

```
FRONTEND LAYER
│
├── Workspaces
│
├── Building Blocks
│
├── Widgets
│
└── Panels
```

## 1. Workspace

Ein Workspace ist eine komplette Arbeitsumgebung.

```
Workspace = Arbeitsbereich
```

Beispiele:

```
Executive Workspace
Portfolio Workspace
Strategy Workspace
Research Workspace
Live Trading Workspace
Risk Workspace
Production Workspace
Data Workspace
Governance Workspace
Management Workspace
```

## 2. Building Block

Ein Building Block ist ein Modul innerhalb eines Workspaces.

Beispiel:

```
Strategy Workspace
│
├── Strategy Repository
├── Strategy Ranking
├── Lifecycle Monitor
├── Regime Analysis
└── Strategy Comparison
```

## 3. Widget

Ein Widget ist eine konkrete Funktion innerhalb eines Building Blocks.

Beispiel:

```
Strategy Ranking
│
├── Top Strategies Widget
├── Bottom Strategies Widget
├── Score Table Widget
└── Rank Change Widget
```

## 4. Panel

Ein Panel ist die sichtbare Kachel/Fenster-Komponente.

Beispiel:

```
Top Strategies Widget
└── Top Strategies Panel
```

## Komplettes Beispiel

```
FRONTEND
│
└── Strategy Workspace
    │
    └── Strategy Ranking
        │
        └── Top Strategies Widget
            │
            └── Top Strategies Panel
```

Kurz:

```
Workspace = Wo arbeite ich?
Building Block = Welches Modul?
Widget = Welche Funktion?
Panel = Was sehe ich?
```