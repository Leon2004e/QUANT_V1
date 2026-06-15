FEEDBACK LOOP

Zweck:

```
Alle Center miteinander verbinden.
```

---

# Der Hauptkreislauf

```
DATA CENTER
↓
STRATEGY CENTER
↓
PORTFOLIO CENTER
↓
EXECUTION CENTER
↓
OPERATIONS CENTER
↓
INTELLIGENCE CENTER
↓
RISK CENTER
↓
GOVERNANCE CENTER
↓
STRATEGY CENTER
```

---

# Schritt 1

DATA CENTER

produziert:

```
Trades
Market Data
Performance Data
```

Output:

```
Baseline Data
Research Data
```

↓

---

# Schritt 2

STRATEGY CENTER

Input:

```
Baseline Data
Research Data
```

berechnet:

```
PF
DD
Winrate
Expectancy
Stability
```

Output:

```
Strategy Score
Strategy Rank
Lifecycle
```

↓

---

# Schritt 3

PORTFOLIO CENTER

Input:

```
Strategy Scores
Lifecycle
Correlation
Risk Metrics
```

berechnet:

```
Portfolio Membership
Portfolio Weights
```

Output:

```
Portfolio Allocation
```

↓

---

# Schritt 4

EXECUTION CENTER

Input:

```
Portfolio Allocation
Risk Limits
Broker Accounts
```

Output:

```
Orders
Executions
Slippage Reports
```

↓

---

# Schritt 5

OPERATIONS CENTER

Input:

```
Orders
Executions
Deployments
```

Output:

```
Live Equity
Live DD
Live Performance
Alerts
```

↓

---

# Schritt 6

INTELLIGENCE CENTER

Input:

```
Alle Outputs
```

Output:

```
Heatmaps
Reports
Analytics
Rankings
```

↓

---

# Schritt 7

RISK CENTER

Input:

```
Portfolio Data
Strategy Data
Execution Data
Live Performance
```

Output:

```
Risk Score
Risk Status
Risk Alerts
```

↓

---

# Schritt 8

GOVERNANCE CENTER

Input:

```
Risk Status
Policies
Thresholds
```

Output:

```
Promotion Rules
Demotion Rules
Retirement Rules
Allocation Rules
```

↓

---

# zurück zum Strategy Center

Governance beeinflusst:

```
Lifecycle
Allocation
Promotion
Retirement
```

Dadurch entsteht:

```
Geschlossener Regelkreis
```

---

# Die wichtigste Kette

```
Trades
↓
Strategy Score
↓
Lifecycle Status
↓
Portfolio Allocation
↓
Orders
↓
Live Performance
↓
Risk Score
↓
Governance Decision
↓
Lifecycle Update
↓
Portfolio Rebalance
↓
Neue Orders
```

---

# Beispiel

EA_145 verliert Edge:

```
90 Day PF
1.75 → 1.12
```

↓

Strategy Center:

```
Score
91 → 63
```

↓

Lifecycle:

```
HOT → COOLING
```

↓

Portfolio Center:

```
12% Gewicht
↓
4% Gewicht
```

↓

Risk Center:

```
Risiko sinkt
```

↓

Governance:

```
Rule G014

Score < 65
↓
Demotion
```

↓

Portfolio Rebalance

↓

Weniger Kapital

↓

System geschützt

---

# Das eigentliche Ziel

Ein Amateur-System macht:

```
Trade
↓
Gewinn/Verlust
```

Dein QUANT OS soll machen:

```
Trade
↓
Performance
↓
Bewertung
↓
Lifecycle
↓
Portfolio Anpassung
↓
Risikoanpassung
↓
Governance
↓
Kapitalanpassung
↓
Neuer Trade
```