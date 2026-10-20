# Startseite für Shopify Dawn 12+ (Mobile-First)

Sektionsaufbau nach dem Vorbild der Toddla-Startseite. Nur natives Liquid und Theme-CSS.
Farben und Schriften kommen ausschliesslich aus den Dawn-Theme-Einstellungen
(Farbschemata `scheme-1`/`scheme-2`, `--font-heading-family`, `--font-body-family`),
deine Markenfarben und Typografie bleiben also erhalten.

## Reihenfolge der Sektionen

| # | Sektion | Datei | UI-Komponenten |
|---|---------|-------|----------------|
| – | Ankündigungsleiste | Dawn `announcement-bar` (Header-Gruppe) | rotierende Ankündigungen, Link |
| – | Header | Dawn `header` (Header-Gruppe) | Logo, Menü, Suche, Konto, Warenkorb, Sticky |
| 1 | Hero | `sections/tdl-hero.liquid` | eigenes Mobile- und Desktop-Bild (`<picture>`), Sternebewertung, H1, Text, 2 Buttons, bis zu 4 Trust-Badges |
| 2 | Trust-Laufband | `sections/tdl-marquee.liquid` | Endlos-Laufband (nur CSS), Icon + Text, optionaler Link, pausiert bei Hover, respektiert `prefers-reduced-motion` |
| 3 | Shoppe nach Alter | `sections/tdl-category-cards.liquid` | wischbare Kacheln (scroll-snap), Bild/Kollektion, Titel, Untertitel, Label, Button |
| 4 | Bestseller | `sections/tdl-product-slider.liquid` | Dawn `card-product`, Slider/Raster, Bewertungssterne, Schnell hinzufügen, „Alle ansehen“ |
| 5 | Vorteile | `sections/tdl-icon-features.liquid` | Icon-Raster 2 Spalten mobil / 2–6 Desktop, Titel, Text |
| 6 | Marken-Story | `sections/tdl-image-text.liquid` | Bild + Inhaltsblöcke: Dachzeile, Überschrift, Text, Checkliste, Kennzahlen, Buttons |
| 7 | Bewertungen | `sections/tdl-reviews.liquid` | Zusammenfassung, Bewertungskarten (Sterne, Titel, Text, Name, verifiziert, Foto, Produktlink) |
| 8 | Bundles | `sections/tdl-product-slider.liquid` (2. Instanz) | wie Bestseller, Raster auf Desktop |
| 9 | Ratgeber/Blog | Dawn `featured-blog` | Beitragskarten |
| 10 | FAQ | `sections/tdl-faq.liquid` | `<details>`-Akkordeon ohne JS, FAQPage-JSON-LD, Kontakt-Button |
| 11 | Newsletter | Dawn `newsletter` | Überschrift, Text, E-Mail-Formular |
| – | Footer | Dawn `footer` (Footer-Gruppe) | Menüs, Social, Zahlungsarten |

## Installation

1. Im Shopify Admin **Onlineshop → Themes → … → Duplizieren** (Backup).
2. **Code bearbeiten** und die Dateien aus diesem Ordner an denselben Pfad kopieren:
   `assets/tdl-home.css`, `snippets/tdl-icon.liquid`, `sections/tdl-*.liquid`.
3. `templates/index.json` ersetzen (oder die Sektionen im Theme-Editor über
   „Sektion hinzufügen“ einzeln einfügen).
4. Im Theme-Editor Bilder, Kollektionen (Bestseller, Bundles) und Texte setzen.

## Playsori-Branding

Logo, Farben und Schriften von Playsori (playsori.de) sind eingebunden:

| Baustein | Wert | Herkunft |
|---|---|---|
| Logo | `F110C948-…_3-removebg-preview.png` (798 × 313, transparent) | Shopify-Dateien des Shops |
| Favicon | `F110C948-….jpg` | Shopify-Dateien des Shops |
| Primär / CTA | `#E91E8C` (Playsori-Pink) | Markenvorgabe |
| Rosa-Akzent | `#ECA2CA` | bisheriges Shop-Theme |
| Zartrosa-Fläche | `#FDF2F8` | aufgehellter Pink-Ton |
| Creme-Fläche | `#FDFBF7` | bisheriges Shop-Theme |
| Text | `#121212` | bisheriges Shop-Theme |
| Überschriften | Quicksand Bold (`quicksand_n7`) | Markenvorgabe |
| Fließtext | Harmonia Sans (`harmonia_sans_n4`) | bisheriges Shop-Theme |

### Farbschemata (Dawn → Theme-Einstellungen → Farben)

| Schema | Hintergrund | Text | Button / Label | Einsatz auf der Startseite |
|---|---|---|---|---|
| scheme-1 | `#FFFFFF` | `#121212` | `#E91E8C` / `#FFFFFF` | Kategorien, Bestseller, Story, Bundles, Blog, FAQ |
| scheme-2 | `#FDF2F8` | `#121212` | `#E91E8C` / `#FFFFFF` | Hero, Vorteile |
| scheme-3 | `#E91E8C` | `#FFFFFF` | `#FFFFFF` / `#E91E8C` | Sale-Badges, grosse Akzentflächen |
| scheme-4 | `#ECA2CA` | `#121212` | `#121212` / `#FFFFFF` | Trust-Laufband, Newsletter |
| scheme-5 | `#FDFBF7` | `#121212` | `#E91E8C` / `#FFFFFF` | Bewertungen |

Sterne, Feature-Icons und Checklisten-Haken übernehmen die Button-Farbe des
Schemas, sind also Playsori-Pink.

Hinweis Lesbarkeit: Weisser Text auf `#E91E8C` hat ein Kontrastverhältnis von
etwa 4,2:1. Das reicht für Buttons und grosse Überschriften, für kleinen
Fliesstext ist scheme-3 daher nicht vorgesehen.

### Übernahme

- **Frisch duplizierter Dawn-Theme:** `playsori/settings_data.json` als
  `config/settings_data.json` hochladen. **Achtung:** Die Datei ersetzt alle
  globalen Theme-Einstellungen; bei einem bereits eingerichteten Theme die
  Werte stattdessen manuell in den Theme-Einstellungen eintragen (Tabellen oben).
- Der Logo-Block in „TDL Bild mit Text“ nutzt automatisch das Logo aus den
  Theme-Einstellungen, ausser du wählst im Block ein eigenes Bild.
