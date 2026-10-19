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
