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

- **Multi-Strategy Hall Parsing:**\
  Automatically detects content type (table, list, text) and uses appropriate parsing strategy\
  for maximum resilience against HTML structure changes.

- **Configurable Pattern Matching:**\
  Uses configurable regex patterns for hall codes, references, and addresses\
  making it easy to adapt to new formats without code changes.

- **Customizable iCal Templates:**\
  Uses your team communication templates for calendar descriptions\
  with dynamic values for dates, times, opponents, and venues.

- **Proper Timezone Handling:**\
  Configurable timezone support with local time or UTC modes\
  for correct event display across different calendar applications.

- **Output Files:**

  - `Spiele_{LEAGUE}_{TEAM}.xlsx` -- filtered matches (e.g. `Spiele_M10C_BSV.xlsx`)\
  - `Hallenverzeichnis_HBV_2025_2026.xlsx` -- parsed hall directory\
  - `Spiele_{LEAGUE}_{TEAM}_mit_Ort.xlsx` -- merged result (matches + hall
    addresses)

---

## 🧰 Requirements

Python ≥ 3.9\
Install dependencies:

```bash
pip install pandas requests beautifulsoup4 lxml openpyxl
```

---

## ⚙️ Configuration

All scripts use a shared configuration file `run.py`. To change the league and team, edit this file:

```python
# Liga und Team die gefiltert werden sollen
TARGET_LEAGUE = "M10A"  # Liga die gefiltert werden sollen
TARGET_TEAM = "BSV"     # Team das gefiltert werden sollen (HEIM oder GAST)
```

**Available Scripts:**
- `run.py` - Main execution script (runs both scripts in sequence)
- `filter.py` - Main filtering and hall data processing
- `table2ical.py` - Convert filtered schedule to iCal format

---

## 🚀 Usage

### Main Execution (Recommended)

```bash
python3 run.py
```

This will run both scripts in sequence:
1. **Filter and process** the schedule and hall data
2. **Convert to calendar** format

### Individual Scripts

#### 1. Filter Schedule and Process Hall Data

```bash
python3 filter.py
```

The script will:
- **Automatically download** the latest schedule from the HBV website
- Load and filter the Excel schedule
- Scrape the official HBV hall directory
- Merge both datasets and export the Excel files

#### 2. Convert to Calendar Format

```bash
python3 table2ical.py
```

The script will:
- Read the filtered schedule with hall data
- Convert all games to iCal format
- Create a calendar file for import into calendar applications

**📅 Calendar Updates**: See `ICAL_UPDATE_GUIDE.md` for detailed information about how calendar updates work and how to handle changes.

**📝 Template Customization**: See `TEMPLATE_GUIDE.md` for detailed information about customizing iCal templates and team communication styles.

### 3. Customize iCal Templates

Edit the template configuration in `run.py`:

```python
# Template selection: 'basic' or 'team'
ICAL_TEMPLATE_TYPE = "team"  # Use "team" for detailed template, "basic" for simple template

# Team-specific information for templates
TEAM_COACH_NAME = "Super Coach"
TEAM_PLAYERS = "Player1 Player1"
TEAM_MEETING_TIME_OFFSET = 45  # Minutes before game start for team meeting

# Timezone configuration for iCal
ICAL_TIMEZONE = "Europe/Berlin"  # German timezone (CET/CEST)
ICAL_USE_LOCAL_TIME = True  # Set to False to use UTC
```

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

`Spiele_{LEAGUE}_{TEAM}.xlsx` Filtered schedule for specified league & team

`Hallenverzeichnis_HBV_2025_2026.xlsx` Parsed hall directory with addresses

`Spiele_{LEAGUE}_{TEAM}_mit_Ort.xlsx` Final dataset with hall addresses & locations

---

---

## 🧩 Customization

### Filter Configuration

You can easily adapt the filters in the script configuration section:

```python
# Filter-Konfiguration
TARGET_LEAGUE = "M10C"  # Liga die gefiltert werden soll
TARGET_TEAM = "BSV"     # Team das gefiltert werden soll (HEIM oder GAST)
```

Change `TARGET_LEAGUE` or `TARGET_TEAM` to your desired league/team.

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
- The system automatically detects HTML structure changes and adapts parsing strategy accordingly.
- Configurable patterns in `run.py` allow easy adaptation to new hall code or address formats.
- iCal templates can be customized in `run.py` with team-specific information and communication style.

## 📁 File Structure

```
python_filter/
├── run.py                             # Main execution script with configuration
├── filter.py                          # Main filtering script
├── table2ical.py                      # Calendar conversion script
├── hall_overrides.json                # Hall data overrides (optional)
├── ICAL_UPDATE_GUIDE.md               # Detailed calendar update guide
├── TEMPLATE_GUIDE.md                  # iCal template customization guide
├── Gesamtspielplan-2025-26_20251002.xlsm  # Downloaded schedule file
├── Gesamtspielplan-2025-26_20251002.xlsx  # Converted schedule file
├── Spiele_{LEAGUE}_{TEAM}.xlsx        # Filtered schedule output
├── Hallenverzeichnis_HBV_2025_2026.xlsx  # Hall directory output
├── Spiele_{LEAGUE}_{TEAM}_mit_Ort.xlsx    # Final merged output
└── Spiele_{LEAGUE}_{TEAM}.ics         # Calendar file output
```

## Extended Info
hallen PDF: https://hamburg-basket.de/wp-content/uploads/2023/06/Hallenverzeichnis-2023-24-Stand-30.06.2023.pdf