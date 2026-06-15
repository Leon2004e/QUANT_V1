QUANT OS Arbeitsregel

QUANT_OS_Overview.md

Definiert die Gesamtarchitektur.
Definiert die Layer.
Definiert die Systemphilosophie.
Definiert die Business Flows.
Definiert die Feedback Loops.
Definiert die Beziehungen zwischen den Layern.

Das Overview dient ausschließlich als:

Orientierung
Gesamtkontext
Systemlandkarte

Nicht als Detail-Spezifikation.

Layer Guides

Jeder Layer besitzt einen eigenen Guide.

Beispiele:

Frontend_Guide.md

Backend_Guide.md

Management_Guide.md

Control_Plane_Guide.md

Infrastructure_Guide.md

Feedback_Loop_Guide.md
Prioritätsregel
Layer Guide
>
Overview

Falls ein Konflikt entsteht:

Der Layer Guide hat Vorrang.
Das Overview wird nicht zur Ergänzung fehlender Details verwendet.
Arbeitsweise

Wenn ein Layer Guide bereitgestellt wird:

Verwende das Overview nur als Gesamtkontext.
Arbeite ausschließlich innerhalb des bereitgestellten Layers.
Nutze nur die Definitionen des Layer Guides.
Erfinde keine zusätzlichen Komponenten.
Erweitere keine Layer eigenständig.
Vermische keine Layer-Details.
Frage bei fehlenden Informationen nach dem entsprechenden Layer Guide.
Beispiel

Wenn du schickst:

QUANT_OS_Overview.md

+

Backend_Guide.md

Dann arbeite ich mit:

Systemkontext:
QUANT_OS_Overview.md

Operative Spezifikation:
Backend_Guide.md

Ich werde dann:

keine Frontend-Komponenten hinzufügen
keine Management-Komponenten ergänzen
keine Infrastructure-Komponenten erfinden
keine neuen Center erzeugen
keine zusätzlichen Workflows definieren

sondern ausschließlich nach dem Backend Guide arbeiten.

Standardverhalten für QUANT OS

Sobald du mir das QUANT OS Overview schickst, gehe ich automatisch davon aus:

Overview = Systemlandkarte

Layer Guide = Spezifikation

Fehlt Detailwissen:
→ nach dem entsprechenden Layer Guide fragen

Nicht:
→ Details aus anderen Layern ableiten
→ Annahmen treffen
→ Komponenten erfinden
LAYER RESPONSIBILITIES

Frontend Layer
Verantwortlich für:
- UI
- Dashboards
- Visualisierung
- Benutzerinteraktion

Backend Layer
Verantwortlich für:
- Datenverarbeitung
- Pipelines
- Strategie-Processing
- Berechnungen
- Analytics

Management Layer
Verantwortlich für:
- Dokumentation
- SOPs
- Layer Guides
- Registries
- Governance
- AI Prompt Management

Control Plane Layer
Verantwortlich für:
- Entscheidungen
- Portfolio-Rotation
- Kapitalallokation
- Freigaben
- Deployment-Steuerung

Infrastructure Layer
Verantwortlich für:
- Hardware
- Server
- Datenbanken
- Storage
- Deployment Infrastruktur

Feedback Loop Layer
Verantwortlich für:
- Monitoring
- Performance Feedback
- Edge Tracking
- Systemverbesserung
- Lifecycle Feedback
# BUILD ORDER

QUANT OS wird grundsätzlich von unten nach oben aufgebaut.

Empfohlene Reihenfolge:

1. Infrastructure Layer
2. Management Layer
3. Control Plane Layer
4. Backend Layer
5. Feedback Loop Layer
6. Frontend Layer

Grundsatz:

Ein Layer sollte erst produktiv entwickelt werden,
wenn die darunterliegenden Layer vorhanden sind.

Frontend wird nicht zuerst gebaut.

Das Frontend ist die letzte Schicht des Systems
und visualisiert die Outputs aller anderen Layer.

Infrastructure bildet die technische Grundlage.
Management verwaltet die Systemobjekte.
Control Plane verbindet das System.
Backend erzeugt die Ergebnisse.
Feedback Loops erzeugen die Selbststeuerung.
Frontend visualisiert und steuert.