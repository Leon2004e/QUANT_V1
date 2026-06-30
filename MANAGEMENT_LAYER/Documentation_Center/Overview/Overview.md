# QUANT OS OVERVIEW

Version: 2.0

---

# PURPOSE

Dieses Dokument definiert ausschließlich die Gesamtarchitektur von QUANT OS.

Es dient als:

- Orientierung
- Systemlandkarte
- Navigation
- Einstiegspunkt

Es ist **keine** Detail-Spezifikation.

Alle technischen Details befinden sich ausschließlich in den Layer Guides und Standards.

---

# DOCUMENTATION HIERARCHY

Overview
↓
Layer Guides
↓
Standards
↓
Registries
↓
Implementierung

Bedeutung:

- Overview = Orientierung
- Layer Guides = Layer-Architektur
- Standards = technische Regeln
- Registries = Verwaltung der Systemobjekte
- Implementierung = Code, Datenbanken, Dashboards, Pipelines

---

# PRIORITY RULE

Bei Konflikten gilt immer:

Standards
>
Layer Guides
>
Overview

---

# WORKING RULE

Das Overview dient ausschließlich dazu,

- den richtigen Layer zu bestimmen,
- den passenden Layer Guide auszuwählen,
- die relevanten Standards zu bestimmen.

Es dürfen keine Spezifikationen ausschließlich aus dem Overview abgeleitet werden.

---

# MANDATORY STARTUP RULE

Diese Regel ist verpflichtend und gilt für **jede neue fachliche Anfrage**.

Vor jeder Analyse, Erklärung, Planung oder Implementierung muss ausschließlich folgender Ablauf durchgeführt werden:

1. Betroffenen Layer bestimmen.
2. Falls nicht eindeutig: "In welchem Layer möchten wir arbeiten?"
3. Prüfen, ob der passende Layer Guide vorliegt.
4. Prüfen, ob die relevanten Standards vorliegen.
5. Nach der konkreten Aufgabe fragen.
6. Nach vorhandenen Komponenten oder bestehenden Implementierungen fragen.
7. Nach Einschränkungen oder Vorgaben fragen.

Erst wenn Punkt 1–7 vollständig geklärt sind, darf mit der eigentlichen Arbeit begonnen werden.

Vorher ist nicht erlaubt:

- Zusammenfassungen
- Analysen
- Architekturvorschläge
- Implementierungen
- Annahmen
- Ergänzungen
- Vermischen von Layern
- Erfinden neuer Komponenten

---

# SYSTEM LAYERS

1. Infrastructure Layer
2. Management Layer
3. Control Plane Layer
4. Backend Layer
5. Feedback Loop Layer
6. Frontend Layer

---

# LAYER RESPONSIBILITIES

## Infrastructure Layer

Storage
Databases
APIs
Scheduler
Logging
Monitoring
Backup
VPS
Automation

## Management Layer

Registries
Catalogs
Configurations
Documentation
Versioning
Audit

## Control Plane Layer

Systemsteuerung
Strategien
Portfolios
Accounts
Deployments
Governance
Events

Kern:
QUANT_SYSTEM.db

## Backend Layer

Verarbeitung
Berechnungen
Analytics
Scoring
Ranking
Lifecycle
Portfolio Construction
Risk Processing

## Feedback Loop Layer

Monitoring
Performance Feedback
Edge Tracking
Lifecycle Feedback
Portfolio Feedback
Governance Feedback
Systemverbesserung

## Frontend Layer

UI
UX
Workspaces
Dashboards
Visualisierung
Benutzerinteraktion

---

# NAVIGATION GUIDE

UI, Dashboards, Workspaces → Frontend_Guide.md

Center, Engines, Analytics, Verarbeitung → Backend_Guide.md

Registries, Catalogs, Dokumentation → Management_Guide.md

Strategien, Portfolios, Accounts, QUANT_SYSTEM.db → Control_Plane_Guide.md

Storage, Datenbanken, APIs, Logging, Monitoring, Backup, Scheduler, VPS, Automation → Infrastructure_Guide.md

Lifecycle, Rotation, Edge Tracking, Rebalancing → Feedback_Loop_Guide.md

---

# BUILD ORDER

QUANT OS wird in folgender Reihenfolge aufgebaut:

1. Infrastructure Layer
2. Management Layer
3. Control Plane Layer
4. Backend Layer
5. Feedback Loop Layer
6. Frontend Layer

Ein Layer darf erst entwickelt werden, wenn alle darunterliegenden Layer definiert sind.

---

# SYSTEM PHILOSOPHY

Infrastructure bildet die Grundlage.

Management verwaltet die Systemobjekte.

Control Plane koordiniert das Gesamtsystem.

Backend verarbeitet Daten und erzeugt Ergebnisse.

Feedback Loops optimieren das System kontinuierlich.

Frontend visualisiert und steuert das System.

---

# PRINCIPLE

Das Overview dient ausschließlich zur Navigation.

Die eigentliche Spezifikation befindet sich immer in:

- Layer Guides
- Standards

Entscheidungen dürfen niemals ausschließlich auf Basis des Overviews getroffen werden.
