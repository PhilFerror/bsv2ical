# 🏀 HBV Schedule Filter & Hall Directory Parser

This Python project automates filtering the **Hamburger Basketball
Verband (HBV)** season schedule and enriches it with **hall location
data** scraped from the official HBV website.

It performs three main tasks: 1. Filters the Excel schedule for a
specific league and club.\
2. Extracts hall details (addresses, postal codes, and additional info)
from the HBV hall directory page.\
3. Merges both datasets to create a complete, location-enhanced
schedule.

---

## ⚙️ Features

- **Excel Filtering:**\
  Filters matches where\
  `Liga = "M10C"` and `(HEIM == "BSV" or GAST == "BSV")`.

- **Column Cleanup:**\
  Keeps only relevant columns:\
  `DATUM, ZEIT, HALLE, HEIM, GAST`.

- **Automatic Schedule Download:**\
  Automatically downloads the latest schedule from\
  <https://hamburg-basket.de/gesamtspielplan/>.\
  Updates every Thursday with the newest version.

- **Web Scraping:**\
  Downloads and parses hall data from\
  <https://hamburg-basket.de/hallen/>.\
  Extracts:

  - Hall code (e.g. `BREH2`)
  - Name / description
  - Address
  - Postal code (PLZ)
  - City / Ort
  - Additional information (e.g. transport hints)

- **Data Merge:**\
  Matches hall codes (e.g. `HBV-BREH2` → `BREH2`)\
  and adds the corresponding address + city to your filtered schedule.

- **JSON Override System:**\
  Manual fine-tuning of hall data via `hall_overrides.json`.\
  Allows correction of scraped data and addition of missing halls.

- **Reference Hall Resolution:**\
  Automatically handles hall codes that reference other halls\
  (e.g. `KGSE2` → inherits data from `KGSE1`).

- **Output Files:**

  - `Spiele_M10C_BSV.xlsx` -- filtered matches\
  - `Hallenverzeichnis_HBV_2025_2026.xlsx` -- parsed hall directory\
  - `Spiele_M10C_BSV_mit_Ort.xlsx` -- merged result (matches + hall
    addresses)

---

## 🧰 Requirements

Python ≥ 3.9\
Install dependencies:

```bash
pip install pandas requests beautifulsoup4 lxml openpyxl
```

---

## 🚀 Usage

### Automatic Mode (Recommended)

1.  Run the script directly:

```bash
python filter.py
```

2.  The script will:
    - **Automatically download** the latest schedule from the HBV website
    - Load and filter the Excel schedule
    - Scrape the official HBV hall directory
    - Merge both datasets and export the Excel files

### Manual Mode

1.  Set `AUTO_DOWNLOAD_SCHEDULE = False` in the script configuration
2.  Place the HBV Excel file (e.g. `Gesamtspielplan-2025-26_20250918.xlsm`) in the project folder
3.  Run the script:

```bash
python filter.py
```

---

## 📂 Output Files

---

File Description

---

`Spiele_M10C_BSV.xlsx` Filtered schedule for Liga M10C & team BSV

`Hallenverzeichnis_HBV_2025_2026.xlsx` Parsed hall directory with addresses

`Spiele_M10C_BSV_mit_Ort.xlsx` Final dataset with hall addresses & locations

---

---

## 🧩 Customization

### Filter Configuration

You can easily adapt the filters in the script:

```python
mask = (df["Liga"] == "M10C") & ((df["HEIM"] == "BSV") | (df["GAST"] == "BSV"))
```

Change `"M10C"` or `"BSV"` to your desired league/team.

### Download Configuration

Control automatic schedule downloading:

```python
AUTO_DOWNLOAD_SCHEDULE = True   # Automatically download latest schedule
AUTO_DOWNLOAD_SCHEDULE = False  # Use local files only
```

When enabled, the script will:
- Check the HBV website for the latest schedule
- Download the newest version automatically
- Use the downloaded file for processing

### Hall Data Overrides

The system includes a JSON-based override system for fine-tuning hall data. Create or edit `hall_overrides.json` to:

#### **Fix Incorrect Data**
```json
{
  "overrides": [
    {
      "kürzel": "ADWG",
      "adresse": "Corrected Address, 12345 Correct City",
      "plz": "12345",
      "ort": "Correct City"
    }
  ]
}
```

#### **Add Missing Halls**
```json
{
  "overrides": [
    {
      "kürzel": "NEWHALL",
      "name_bezeichnung": "New Hall",
      "adresse": "New Street 100, 20000 Hamburg",
      "plz": "20000",
      "ort": "Hamburg",
      "zusatzinfo": "Directions and access information"
    }
  ]
}
```

#### **JSON Structure**
- `kürzel`: Hall code (required) - must match exactly with hall codes in the schedule
- `name_bezeichnung`: Hall name/type (optional) - will replace scraped name
- `adresse`: Full address (optional) - will replace scraped address
- `plz`: Postal code (optional) - will replace scraped postal code
- `ort`: City name (optional) - will replace scraped city
- `zusatzinfo`: Additional information like directions, notes (optional)

#### **Behavior**
- **Update Existing**: If hall code exists in scraped data, fields will be updated
- **Add New**: If hall code doesn't exist, a new hall entry will be created
- **Override Priority**: JSON overrides take precedence over scraped data

---

## ⚠️ Notes

- The HBV hall directory's format may vary slightly between seasons.\
  The parser is designed to handle common cases but may need
  adjustment if the website layout changes.
- "HH" in addresses is automatically converted to "Hamburg".
- Hall codes with spaces (e.g. "PEPE 1", "PEPE 2") are supported.
- Hall codes with German umlauts (Ä, Ö, Ü) are supported.
- Reference halls (e.g. "KGSE2: Siehe KGSE1") are automatically resolved.
- Parentheses hints (e.g. "(eh. BÖTT)") are treated as additional information.
- If a hall code is missing on the HBV site, use the JSON override system to add it manually.

## 📁 File Structure

```
python_filter/
├── filter.py                          # Main script
├── hall_overrides.json                # Hall data overrides (optional)
├── Gesamtspielplan-2025-26_20251002.xlsm  # Downloaded schedule file
├── Gesamtspielplan-2025-26_20251002.xlsx  # Converted schedule file
├── Spiele_M10C_BSV.xlsx              # Filtered schedule output
├── Hallenverzeichnis_HBV_2025_2026.xlsx  # Hall directory output
└── Spiele_M10C_BSV_mit_Ort.xlsx      # Final merged output
```

## Extended Info
hallen PDF: https://hamburg-basket.de/wp-content/uploads/2023/06/Hallenverzeichnis-2023-24-Stand-30.06.2023.pdf