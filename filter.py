# -*- coding: utf-8 -*-
"""
HBV schedule filter + hall directory scraper/merger
Requirements: pandas, requests, beautifulsoup4, lxml (optional but recommended), openpyxl
> pip install pandas requests beautifulsoup4 lxml openpyxl
"""

import re
import pandas as pd
import requests
from bs4 import BeautifulSoup
import openpyxl
from openpyxl import load_workbook
import json
import os

# -----------------------------
# 1) Shared Configuration
# -----------------------------
from run import (
    TARGET_LEAGUE, TARGET_TEAM,
    SCHEDULE_XLSM, SCHEDULE_XLSX, SCHEDULE_SHEET,
    HALLS_URL, SCHEDULE_URL, HALL_OVERRIDES_JSON,
    OUT_FILTERED_XLSX, OUT_HALLS_XLSX, OUT_MERGED_XLSX,
    AUTO_DOWNLOAD_SCHEDULE,
    HALL_CODE_PATTERNS, REFERENCE_PATTERNS, ADDRESS_PATTERNS
)

# -----------------------------
# 2) Gesamtspielplan von Website herunterladen
# -----------------------------
def download_latest_schedule(url=SCHEDULE_URL, timeout=30):
    """
    Lädt die neueste Gesamtspielplan-Datei von der HBV-Website herunter.
    
    Args:
        url (str): URL der Gesamtspielplan-Seite
        timeout (int): Timeout für HTTP-Requests
        
    Returns:
        str: Pfad zur heruntergeladenen Datei oder None bei Fehler
    """
    try:
        print("Lade Gesamtspielplan-Seite...")
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, 'lxml')
        
        # Suche nach Download-Links für XLSM/XLSX-Dateien
        download_links = []
        
        # Suche nach direkten Links zu Excel-Dateien
        for link in soup.find_all('a', href=True):
            href = link['href']
            if any(ext in href.lower() for ext in ['.xlsm', '.xlsx']):
                # Vollständige URL erstellen falls nötig
                if href.startswith('/'):
                    href = 'https://hamburg-basket.de' + href
                elif not href.startswith('http'):
                    href = url + href
                download_links.append(href)
        
        # Suche nach Links mit "Gesamtspielplan" im Text
        for link in soup.find_all('a', href=True):
            link_text = link.get_text(strip=True).lower()
            if 'gesamtspielplan' in link_text and any(ext in link['href'].lower() for ext in ['.xlsm', '.xlsx']):
                href = link['href']
                if href.startswith('/'):
                    href = 'https://hamburg-basket.de' + href
                elif not href.startswith('http'):
                    href = url + href
                download_links.append(href)
        
        if not download_links:
            print("Keine Gesamtspielplan-Datei auf der Website gefunden.")
            return None
        
        # Nimm den ersten gefundenen Link (normalerweise der neueste)
        download_url = download_links[0]
        print(f"Gefundene Datei: {download_url}")
        
        # Dateiname aus URL extrahieren
        filename = download_url.split('/')[-1]
        if not filename.endswith(('.xlsm', '.xlsx')):
            # Fallback: generiere Dateinamen
            filename = f"Gesamtspielplan-{pd.Timestamp.now().strftime('%Y-%m-%d')}.xlsm"
        
        # Datei herunterladen
        print(f"Lade {filename} herunter...")
        file_response = requests.get(download_url, timeout=timeout)
        file_response.raise_for_status()
        
        # Datei speichern
        with open(filename, 'wb') as f:
            f.write(file_response.content)
        
        print(f"Erfolgreich heruntergeladen: {filename}")
        return filename
        
    except requests.RequestException as e:
        print(f"Fehler beim Herunterladen der Gesamtspielplan-Datei: {e}")
        return None
    except Exception as e:
        print(f"Unerwarteter Fehler beim Herunterladen: {e}")
        return None

# -----------------------------
# 3) XLSM zu XLSX Konvertierung
# -----------------------------
def convert_xlsm_to_xlsx(xlsm_path, xlsx_path):
    """
    Konvertiert eine XLSM-Datei zu XLSX-Format.
    Entfernt alle VBA-Makros und behält nur die Daten.
    
    Args:
        xlsm_path (str): Pfad zur XLSM-Datei
        xlsx_path (str): Pfad für die ausgegebene XLSX-Datei
    """
    try:
        # XLSM-Datei laden
        wb = load_workbook(xlsm_path, keep_vba=False)
        
        # Als XLSX speichern (ohne VBA)
        wb.save(xlsx_path)
        print(f"Konvertierung erfolgreich: {xlsm_path} -> {xlsx_path}")
        return True
        
    except Exception as e:
        print(f"Fehler bei der Konvertierung von {xlsm_path}: {e}")
        return False

# -----------------------------
# 3) Excel laden & filtern
# -----------------------------
def load_and_filter_schedule(path=SCHEDULE_XLSX, sheet=SCHEDULE_SHEET):
    df = pd.read_excel(path, sheet_name=sheet)
    # Filter: Liga = TARGET_LEAGUE und (HEIM = TARGET_TEAM oder GAST = TARGET_TEAM)
    mask = (df["LIGA"] == TARGET_LEAGUE) & ((df["HEIM"] == TARGET_TEAM) | (df["GAST"] == TARGET_TEAM))
    filtered = df.loc[mask, ["DATUM", "ZEIT", "HALLE", "HEIM", "GAST"]].reset_index(drop=True)
    return filtered

# -----------------------------
# 4) Hallenseite laden (HTML)
# -----------------------------
def fetch_halls_html(url=HALLS_URL, timeout=30):
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.text

# -----------------------------
# 4.1) Content type detection and validation
# -----------------------------
def detect_content_type(soup):
    """
    Detect the type of content structure used for hall data.
    
    Args:
        soup (BeautifulSoup): Parsed HTML content
        
    Returns:
        str: Content type ('table', 'list', 'text', 'unknown')
    """
    # Check for tables first
    tables = soup.find_all('table')
    if tables:
        # Validate if tables contain hall-like data
        for table in tables:
            if contains_hall_data_in_table(table):
                return 'table'
    
    # Check for lists
    lists = soup.find_all(['ul', 'ol'])
    if lists:
        for list_elem in lists:
            if contains_hall_data_in_list(list_elem):
                return 'list'
    
    # Check for text-based content
    text_content = soup.get_text()
    if contains_hall_data_in_text(text_content):
        return 'text'
    
    return 'unknown'

def contains_hall_data_in_table(table):
    """
    Check if a table contains hall data by looking for hall codes.
    
    Args:
        table: BeautifulSoup table element
        
    Returns:
        bool: True if table contains hall data
    """
    rows = table.find_all('tr')
    hall_code_count = 0
    
    for row in rows[:10]:  # Check first 10 rows
        cells = row.find_all(['td', 'th'])
        for cell in cells:
            text = cell.get_text(strip=True)
            if matches_hall_code_pattern(text):
                hall_code_count += 1
                if hall_code_count >= 2:  # Found at least 2 hall codes
                    return True
    
    return hall_code_count >= 1

def contains_hall_data_in_list(list_elem):
    """
    Check if a list contains hall data.
    
    Args:
        list_elem: BeautifulSoup list element
        
    Returns:
        bool: True if list contains hall data
    """
    items = list_elem.find_all('li')
    hall_code_count = 0
    
    for item in items[:10]:  # Check first 10 items
        text = item.get_text(strip=True)
        if matches_hall_code_pattern(text):
            hall_code_count += 1
            if hall_code_count >= 2:
                return True
    
    return hall_code_count >= 1

def contains_hall_data_in_text(text):
    """
    Check if text content contains hall data.
    
    Args:
        text (str): Text content
        
    Returns:
        bool: True if text contains hall data
    """
    lines = text.split('\n')
    hall_code_count = 0
    
    for line in lines[:50]:  # Check first 50 lines
        line = line.strip()
        if matches_hall_code_pattern(line):
            hall_code_count += 1
            if hall_code_count >= 3:  # Need more for text-based
                return True
    
    return hall_code_count >= 2

def matches_hall_code_pattern(text):
    """
    Check if text matches any of the configured hall code patterns.
    
    Args:
        text (str): Text to check
        
    Returns:
        bool: True if text matches a hall code pattern
    """
    if not text or len(text) > 10:  # Hall codes are typically short
        return False
    
    for pattern in HALL_CODE_PATTERNS:
        if re.match(pattern, text):
            return True
    
    return False

def contains_address_pattern(text):
    """
    Check if text contains address patterns using configurable patterns.
    
    Args:
        text (str): Text to check
        
    Returns:
        bool: True if text contains address patterns
    """
    for pattern in ADDRESS_PATTERNS:
        if re.search(pattern, text):
            return True
    return False

def extract_address_components(text, hall_dict):
    """
    Extract postal code and city from address text.
    
    Args:
        text (str): Address text
        hall_dict (dict): Hall dictionary to update
    """
    # Extract PLZ
    plz_match = re.search(r'(\d{5})', text)
    if plz_match:
        hall_dict["PLZ"] = plz_match.group(1)
    
    # Extract city
    if 'HH' in text:
        hall_dict["Ort"] = "Hamburg"
    elif 'Hamburg' in text:
        hall_dict["Ort"] = "Hamburg"
    else:
        # Try to extract city name after postal code
        city_match = re.search(r'\d{5}\s+([A-Za-zÄÖÜäöüß\s]+)', text)
        if city_match:
            hall_dict["Ort"] = city_match.group(1).strip()

# -----------------------------
# 5) Hallentext aus Seite ziehen
#    (die Seite hat meist lange Textblöcke)
# -----------------------------
def extract_halls_text(html):
    soup = BeautifulSoup(html, "lxml")
    # Heuristik: Haupt-Content sammeln
    # Nimm alle Textknoten im Inhaltsbereich (WP-typisch .entry-content)
    candidates = soup.select(".entry-content, article, main, .post-content, .content")
    if not candidates:
        # Fallback: ganze Seite als Text
        text = soup.get_text("\n", strip=True)
    else:
        text = "\n".join(c.get_text("\n", strip=True) for c in candidates)
    # Manche Seiten haben sehr viel "Menü" etc. – wir schneiden am "Hallenverzeichnis" an,
    # wenn vorhanden:
    # (Optional; auskommentiert, falls nicht nötig)
    # m = re.search(r"Hallenverzeichnis.*", text, flags=re.I|re.S)
    # if m:
    #     text = m.group(0)
    return text

# -----------------------------
# 6) Hallentext in Blöcke zerlegen
#    Blöcke sind meist durch Leerzeilen getrennt
# -----------------------------
def split_blocks(raw_text):
    blocks = [b.strip() for b in re.split(r"\n\s*\n", raw_text) if b.strip()]
    # filtern wir grob Offensichtliches raus (z.B. Navigationsreste)
    # Falls nötig, könnte man hier heuristischer filtern – wir lassen erstmal alles drin
    return blocks

# -----------------------------
# 7) Einen Block robust parsen
#    Formate lt. Beschreibung:
#    - Erste Zeile beginnt mit Hallenkürzel (ADWG, OHK, BREH2, ...),
#      danach Hallenname/Bezeichnung (manchmal auch "Verbandshalle ...")
#    - Adressen stehen meist in einer der Folgezeilen, oft mit Komma+PLZ
#    - Zusatzinfo kann 0..n Zeilen danach sein
# -----------------------------
CODE_RE = re.compile(r"^([A-ZÄÖÜ]{2,}[0-9]?)\b\s*(.*)$")  # Kürzel (2+ Großbuchstaben + optional Ziffer)

def parse_block(block):
    lines = [l.strip() for l in block.splitlines() if l.strip()]
    if not lines:
        return None

    # 6.1 Kürzel + (optionaler) Name in Zeile 1
    code, name = "", ""
    m = CODE_RE.match(lines[0])
    if m:
        code = m.group(1).strip()
        name = m.group(2).strip()
    else:
        # Falls erste Zeile kein Kürzel führt, ignorieren wir den Block
        return None

    # 6.2 Adresse finden: erste Zeile nach der ersten,
    #     die eine 5-stellige PLZ enthält oder zumindest Komma + Zahl(en)
    address_line = ""
    address_idx = None
    for idx, l in enumerate(lines[1:], start=1):
        if re.search(r"\b\d{5}\b", l) and "," in l:
            address_line = l
            address_idx = idx
            break
    if not address_line:
        # fallback: nimm zweite Zeile, wenn vorhanden
        if len(lines) > 1:
            address_line = lines[1]
            address_idx = 1
        else:
            address_line = ""
            address_idx = None

    # 6.3 Zusatzinfo = alles nach der Adresszeile
    extra = ""
    if address_idx is not None and address_idx + 1 < len(lines):
        extra = " ".join(lines[address_idx + 1:]).strip()

    # 6.4 PLZ / Ort extrahieren (robust, HH => Hamburg)
    plz = ""
    ort = ""
    # Suche am Ende: ", 22359 HH" oder ", 22359 Hamburg" o.ä.
    m_plz = re.search(r"(\d{5})\s*([A-Za-zÄÖÜäöüß\-\.\(\)\/ ]+)?$", address_line)
    if m_plz:
        plz = m_plz.group(1)
        ort_raw = (m_plz.group(2) or "").strip(" ,")
        if ort_raw == "HH":
            ort = "Hamburg"
        else:
            ort = ort_raw

    return {
        "Kürzel": code,
        "Name / Bezeichnung": name,
        "Adresse": address_line,
        "PLZ": plz,
        "Ort": ort,
        "Zusatzinfo": extra
    }

# -----------------------------
# 8) Special handling for hall codes that reference other halls
# -----------------------------
def handle_reference_halls(halls_df):
    """
    Handle hall codes that reference other halls (e.g., KGSE2 -> KGSE1).
    These halls inherit data from their base hall code.
    
    This method looks for hall entries where the "Name / Bezeichnung" field
    contains reference patterns like "Siehe KGSE1" and creates a new hall
    entry with the same data as the referenced hall but with the original
    hall code preserved.
    
    Supported reference patterns:
    - "Siehe KGSE1" / "siehe KGSE1"
    - "Vgl. KGSE1" (Vergleich/Compare)
    
    Args:
        halls_df (pd.DataFrame): DataFrame with hall data
        
    Returns:
        pd.DataFrame: Updated DataFrame with reference halls resolved
    """
    # Find halls that reference other halls (using configurable patterns)
    reference_patterns = REFERENCE_PATTERNS
    
    reference_halls = []
    base_halls = {}
    
    # First pass: identify reference halls and build base hall lookup
    for idx, row in halls_df.iterrows():
        hall_code = row['Kürzel']
        name = str(row['Name / Bezeichnung']).strip()
        
        # Check if this is a reference hall
        is_reference = False
        base_code = None
        
        for pattern in reference_patterns:
            match = re.match(pattern, name, re.IGNORECASE)
            if match:
                base_code = match.group(1).upper()
                is_reference = True
                break
        
        if is_reference and base_code:
            reference_halls.append((idx, hall_code, base_code))
        else:
            # This is a base hall - store for reference
            base_halls[hall_code] = row
    
    print(f"Found {len(reference_halls)} reference halls:")
    for idx, ref_code, base_code in reference_halls:
        print(f"  {ref_code} -> {base_code}")
    
    # Second pass: resolve reference halls
    resolved_halls = []
    for idx, ref_code, base_code in reference_halls:
        if base_code in base_halls:
            # Create new hall entry based on base hall
            base_hall = base_halls[base_code].copy()
            base_hall['Kürzel'] = ref_code  # Keep the reference hall code
            base_hall['Name / Bezeichnung'] = f"{base_hall['Name / Bezeichnung']} (Referenz: {base_code})"
            resolved_halls.append(base_hall)
            print(f"  Resolved {ref_code} using data from {base_code}")
        else:
            print(f"  Warning: Base hall {base_code} not found for reference {ref_code}")
    
    # Remove original reference halls and add resolved ones
    if reference_halls:
        # Remove reference hall rows
        reference_indices = [idx for idx, _, _ in reference_halls]
        halls_df_cleaned = halls_df.drop(reference_indices).reset_index(drop=True)
        
        # Add resolved halls
        if resolved_halls:
            resolved_df = pd.DataFrame(resolved_halls)
            halls_df_final = pd.concat([halls_df_cleaned, resolved_df], ignore_index=True)
        else:
            halls_df_final = halls_df_cleaned
    else:
        halls_df_final = halls_df
    
    return halls_df_final

# -----------------------------
# 9) Load and apply manual hall overrides from JSON file
# -----------------------------
def apply_hall_overrides(halls_df, json_file=HALL_OVERRIDES_JSON):
    """
    Load manual hall overrides from JSON file and apply them to the halls DataFrame.
    
    This allows fine-tuning of hall data by manually specifying hall codes and addresses
    that will override the scraped data.
    
    Args:
        halls_df (pd.DataFrame): DataFrame with scraped hall data
        json_file (str): Path to the JSON override file
        
    Returns:
        pd.DataFrame: Updated DataFrame with overrides applied
    """
    if not os.path.exists(json_file):
        print(f"Override file {json_file} not found. Skipping manual overrides.")
        return halls_df
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            override_data = json.load(f)
        
        overrides = override_data.get('overrides', [])
        if not overrides:
            print("No overrides found in JSON file.")
            return halls_df
        
        print(f"Loading {len(overrides)} manual hall overrides...")
        
        # Create a copy of the DataFrame to avoid modifying the original
        halls_df_updated = halls_df.copy()
        
        for override in overrides:
            kürzel = override.get('kürzel', '').strip()
            if not kürzel:
                print("Warning: Override entry missing 'kürzel' field, skipping.")
                continue
            
            # Check if this hall already exists
            existing_mask = halls_df_updated['Kürzel'] == kürzel
            
            if existing_mask.any():
                # Update existing hall
                print(f"  Updating existing hall: {kürzel}")
                for field, value in override.items():
                    if field != 'kürzel' and value:  # Skip empty values and kürzel
                        # Map JSON field names to DataFrame column names
                        column_map = {
                            'name_bezeichnung': 'Name / Bezeichnung',
                            'adresse': 'Adresse',
                            'plz': 'PLZ',
                            'ort': 'Ort',
                            'zusatzinfo': 'Zusatzinfo'
                        }
                        if field in column_map:
                            halls_df_updated.loc[existing_mask, column_map[field]] = value
            else:
                # Add new hall
                print(f"  Adding new hall: {kürzel}")
                new_hall = {
                    'Kürzel': kürzel,
                    'Name / Bezeichnung': override.get('name_bezeichnung', ''),
                    'Adresse': override.get('adresse', ''),
                    'PLZ': override.get('plz', ''),
                    'Ort': override.get('ort', ''),
                    'Zusatzinfo': override.get('zusatzinfo', '')
                }
                
                # Add the new hall to the DataFrame
                new_row_df = pd.DataFrame([new_hall])
                halls_df_updated = pd.concat([halls_df_updated, new_row_df], ignore_index=True)
        
        print(f"Manual overrides applied successfully.")
        return halls_df_updated
        
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON file {json_file}: {e}")
        return halls_df
    except Exception as e:
        print(f"Error loading overrides from {json_file}: {e}")
        return halls_df

# -----------------------------
# 10) Gesamtes Hallenverzeichnis extrahieren (Multi-strategy)
# -----------------------------
def scrape_halls_table(url=HALLS_URL):
    """
    Extract hall data using multiple strategies for maximum resilience.
    
    Args:
        url (str): URL to scrape hall data from
        
    Returns:
        pd.DataFrame: Hall data with columns: Kürzel, Name / Bezeichnung, Adresse, PLZ, Ort, Zusatzinfo
    """
    try:
        html = fetch_halls_html(url)
        soup = BeautifulSoup(html, "lxml")
        
        # Detect content type and choose appropriate parsing strategy
        content_type = detect_content_type(soup)
        print(f"Detected content type: {content_type}")
        
        if content_type == 'table':
            return scrape_halls_from_tables(soup)
        elif content_type == 'list':
            return scrape_halls_from_lists(soup)
        elif content_type == 'text':
            return scrape_halls_from_text(soup)
        else:
            print("Warnung: Unbekannter Content-Typ. Versuche Table-Parsing als Fallback.")
            return scrape_halls_from_tables(soup)
            
    except Exception as e:
        print(f"Fehler beim Scraping der Hallendaten: {e}")
        return pd.DataFrame(columns=["Kürzel", "Name / Bezeichnung", "Adresse", "PLZ", "Ort", "Zusatzinfo"])

def scrape_halls_from_tables(soup):
    """
    Extract hall data from HTML tables with multiple table support.
    
    Args:
        soup (BeautifulSoup): Parsed HTML content
        
    Returns:
        pd.DataFrame: Hall data
    """
    # Find all tables containing hall data
    tables = soup.find_all('table')
    if not tables:
        print("Warnung: Keine Tabelle gefunden. Erstelle leere DataFrame.")
        return pd.DataFrame(columns=["Kürzel", "Name / Bezeichnung", "Adresse", "PLZ", "Ort", "Zusatzinfo"])
    
    # Try each table until we find one with hall data
    for i, table in enumerate(tables):
        if contains_hall_data_in_table(table):
            print(f"Verwende Tabelle {i+1} von {len(tables)} für Hallendaten")
            return parse_table_for_halls(table)
    
    print("Warnung: Keine Tabelle mit Hallendaten gefunden. Erstelle leere DataFrame.")
    return pd.DataFrame(columns=["Kürzel", "Name / Bezeichnung", "Adresse", "PLZ", "Ort", "Zusatzinfo"])

def parse_table_for_halls(table):
    """
    Parse a single table for hall data.
    
    Args:
        table: BeautifulSoup table element
        
    Returns:
        pd.DataFrame: Hall data
    """
    rows = table.find_all('tr')
    entries = []
    current_hall = None
    
    for i, row in enumerate(rows):
        cells = row.find_all(['td', 'th'])
        cell_texts = [cell.get_text(strip=True) for cell in cells]
        
        # Skip empty rows
        if not any(cell_texts):
            continue
            
        # Skip rows that start with text in parentheses (like "(eh. BÖTT)") - these are hints for previous hall
        if cell_texts and cell_texts[0].startswith('(') and cell_texts[0].endswith(')'):
            # This is additional information for the current hall
            if current_hall and cell_texts:
                info_text = " ".join(cell_texts).strip()
                # Check if this looks like an address using configurable patterns
                if contains_address_pattern(info_text):
                    if not current_hall["Adresse"]:
                        current_hall["Adresse"] = info_text
                        extract_address_components(info_text, current_hall)
                else:
                    # Additional info (directions, notes, etc.)
                    if current_hall["Zusatzinfo"]:
                        current_hall["Zusatzinfo"] += " | " + info_text
                    else:
                        current_hall["Zusatzinfo"] = info_text
            continue
            
        # Check if this row contains a hall code using configurable patterns
        if cell_texts and matches_hall_code_pattern(cell_texts[0]) and len(cell_texts[0]) <= 6:
            # Save previous hall if exists
            if current_hall:
                entries.append(current_hall)
            
            # Start new hall entry
            current_hall = {
                "Kürzel": cell_texts[0],
                "Name / Bezeichnung": "",
                "Adresse": "",
                "PLZ": "",
                "Ort": "",
                "Zusatzinfo": ""
            }
            
            # Check if second cell contains address using configurable patterns
            if len(cell_texts) > 1 and contains_address_pattern(cell_texts[1]):
                # Address is in the same row
                current_hall["Adresse"] = cell_texts[1]
                extract_address_components(cell_texts[1], current_hall)
                
                # Additional info from remaining cells
                if len(cell_texts) > 2:
                    current_hall["Zusatzinfo"] = " ".join(cell_texts[2:]).strip()
            else:
                # Standard format: hall type/name in second cell, address in subsequent rows
                current_hall["Name / Bezeichnung"] = cell_texts[1] if len(cell_texts) > 1 else ""
                
                # Add additional info from same row
                if len(cell_texts) > 2:
                    current_hall["Zusatzinfo"] = " ".join(cell_texts[2:]).strip()
                
        elif current_hall and cell_texts:
            # This is additional information for the current hall
            info_text = " ".join(cell_texts).strip()
            
            # Check if this looks like an address using configurable patterns
            if contains_address_pattern(info_text):
                if not current_hall["Adresse"]:
                    current_hall["Adresse"] = info_text
                    extract_address_components(info_text, current_hall)
            else:
                # Additional info (directions, notes, etc.)
                if current_hall["Zusatzinfo"]:
                    current_hall["Zusatzinfo"] += " | " + info_text
                else:
                    current_hall["Zusatzinfo"] = info_text
    
    # Don't forget the last hall
    if current_hall:
        entries.append(current_hall)
    
    print(f"Gefunden {len(entries)} Hallen in der Tabelle")

    # Check if we found any entries
    if not entries:
        print("Warnung: Keine Hallen gefunden. Erstelle leere DataFrame.")
        return pd.DataFrame(columns=["Kürzel", "Name / Bezeichnung", "Adresse", "PLZ", "Ort", "Zusatzinfo"])
    
    # Create DataFrame and clean up
    halls_df = pd.DataFrame(entries)
    halls_df["Kürzel"] = halls_df["Kürzel"].str.strip()
    halls_df["Adresse"] = halls_df["Adresse"].str.strip(", ").str.replace(" ,", ",", regex=False)
    halls_df["Ort"] = halls_df["Ort"].str.replace("HH", "Hamburg")
    
    # Handle reference halls (e.g., KGSE2 -> KGSE1)
    halls_df = handle_reference_halls(halls_df)
    
    # Apply manual overrides from JSON file
    halls_df = apply_hall_overrides(halls_df)
    
    return halls_df

def scrape_halls_from_lists(soup):
    """
    Extract hall data from HTML lists (ul/ol elements).
    
    Args:
        soup (BeautifulSoup): Parsed HTML content
        
    Returns:
        pd.DataFrame: Hall data
    """
    lists = soup.find_all(['ul', 'ol'])
    if not lists:
        print("Warnung: Keine Listen gefunden. Erstelle leere DataFrame.")
        return pd.DataFrame(columns=["Kürzel", "Name / Bezeichnung", "Adresse", "PLZ", "Ort", "Zusatzinfo"])
    
    # Try each list until we find one with hall data
    for i, list_elem in enumerate(lists):
        if contains_hall_data_in_list(list_elem):
            print(f"Verwende Liste {i+1} von {len(lists)} für Hallendaten")
            return parse_list_for_halls(list_elem)
    
    print("Warnung: Keine Liste mit Hallendaten gefunden. Erstelle leere DataFrame.")
    return pd.DataFrame(columns=["Kürzel", "Name / Bezeichnung", "Adresse", "PLZ", "Ort", "Zusatzinfo"])

def parse_list_for_halls(list_elem):
    """
    Parse a list element for hall data.
    
    Args:
        list_elem: BeautifulSoup list element
        
    Returns:
        pd.DataFrame: Hall data
    """
    items = list_elem.find_all('li')
    entries = []
    
    for item in items:
        text = item.get_text(strip=True)
        if not text:
            continue
        
        # Try to extract hall code from the beginning of the text
        lines = text.split('\n')
        if not lines:
            continue
        
        first_line = lines[0].strip()
        if matches_hall_code_pattern(first_line):
            hall_entry = {
                "Kürzel": first_line,
                "Name / Bezeichnung": "",
                "Adresse": "",
                "PLZ": "",
                "Ort": "",
                "Zusatzinfo": ""
            }
            
            # Process remaining lines for address and additional info
            for line in lines[1:]:
                line = line.strip()
                if not line:
                    continue
                
                if contains_address_pattern(line):
                    if not hall_entry["Adresse"]:
                        hall_entry["Adresse"] = line
                        extract_address_components(line, hall_entry)
                else:
                    if hall_entry["Zusatzinfo"]:
                        hall_entry["Zusatzinfo"] += " | " + line
                    else:
                        hall_entry["Zusatzinfo"] = line
            
            entries.append(hall_entry)
    
    print(f"Gefunden {len(entries)} Hallen in der Liste")
    
    if not entries:
        return pd.DataFrame(columns=["Kürzel", "Name / Bezeichnung", "Adresse", "PLZ", "Ort", "Zusatzinfo"])
    
    # Create DataFrame and process
    halls_df = pd.DataFrame(entries)
    halls_df["Kürzel"] = halls_df["Kürzel"].str.strip()
    halls_df["Adresse"] = halls_df["Adresse"].str.strip(", ").str.replace(" ,", ",", regex=False)
    halls_df["Ort"] = halls_df["Ort"].str.replace("HH", "Hamburg")
    
    # Handle reference halls and apply overrides
    halls_df = handle_reference_halls(halls_df)
    halls_df = apply_hall_overrides(halls_df)
    
    return halls_df

def scrape_halls_from_text(soup):
    """
    Extract hall data from text-based content using the legacy text parsing method.
    
    Args:
        soup (BeautifulSoup): Parsed HTML content
        
    Returns:
        pd.DataFrame: Hall data
    """
    print("Verwende Text-basiertes Parsing als Fallback")
    
    # Use the existing text-based parsing logic
    html = str(soup)
    text = extract_halls_text(html)
    blocks = split_blocks(text)
    
    entries = []
    for block in blocks:
        parsed = parse_block(block)
        if parsed:
            entries.append(parsed)
    
    print(f"Gefunden {len(entries)} Hallen im Text")
    
    if not entries:
        return pd.DataFrame(columns=["Kürzel", "Name / Bezeichnung", "Adresse", "PLZ", "Ort", "Zusatzinfo"])
    
    # Create DataFrame and process
    halls_df = pd.DataFrame(entries)
    halls_df["Kürzel"] = halls_df["Kürzel"].str.strip()
    halls_df["Adresse"] = halls_df["Adresse"].str.strip(", ").str.replace(" ,", ",", regex=False)
    halls_df["Ort"] = halls_df["Ort"].str.replace("HH", "Hamburg")
    
    # Handle reference halls and apply overrides
    halls_df = handle_reference_halls(halls_df)
    halls_df = apply_hall_overrides(halls_df)
    
    return halls_df

# -----------------------------
# 9) HALLE → Hallenkürzel ableiten, z.B. "HBV-BREH2" → "BREH2"
# -----------------------------
def extract_hall_code(hall_value):
    if pd.isna(hall_value):
        return ""
    # Übliche Form: "HBV-XXXX" oder "HBV-XXXXn"
    m = re.search(r"HBV-([A-ZÄÖÜ]{2,}[0-9]?)", str(hall_value))
    if m:
        extracted = m.group(1)
        # Special handling for PEPE halls: HBV-PEPE2 -> PEPE 2
        if extracted == "PEPE2":
            return "PEPE 2"
        elif extracted == "PEPE1":
            return "PEPE 1"
        return extracted
    # Fallback: wenn doch direkt ein Code drinsteht:
    m2 = re.search(r"\b([A-ZÄÖÜ]{2,}[0-9]?)\b", str(hall_value))
    return m2.group(1) if m2 else ""

# -----------------------------
# 10) Merge: Gefilterter Spielplan + Hallentabelle
# -----------------------------
def merge_schedule_with_halls(filtered_df, halls_df):
    tmp = filtered_df.copy()
    tmp["Kürzel"] = tmp["HALLE"].apply(extract_hall_code)
    merged = tmp.merge(halls_df[["Kürzel", "Adresse", "PLZ", "Ort"]], on="Kürzel", how="left")
    # Sinnvolle Spaltenreihenfolge
    merged = merged[["DATUM", "ZEIT", "HALLE", "Kürzel", "Ort", "PLZ", "Adresse", "HEIM", "GAST"]]
    return merged

# -----------------------------
# 11) Main: ausführen
# -----------------------------
if __name__ == "__main__":
    # a) Neueste Gesamtspielplan-Datei herunterladen (optional)
    schedule_file = SCHEDULE_XLSM
    if AUTO_DOWNLOAD_SCHEDULE:
        print("Versuche neueste Gesamtspielplan-Datei von Website zu laden...")
        downloaded_file = download_latest_schedule()
        if downloaded_file:
            schedule_file = downloaded_file
            # Aktualisiere auch den XLSX-Pfad
            schedule_xlsx = downloaded_file.replace('.xlsm', '.xlsx').replace('.xlsx', '.xlsx')
        else:
            print("Download fehlgeschlagen. Verwende lokale Datei.")
            schedule_xlsx = SCHEDULE_XLSX
    else:
        schedule_xlsx = SCHEDULE_XLSX
    
    # b) XLSM zu XLSX konvertieren
    print("Konvertiere XLSM zu XLSX...")
    if not convert_xlsm_to_xlsx(schedule_file, schedule_xlsx):
        print("Konvertierung fehlgeschlagen. Verwende vorhandene XLSX-Datei falls vorhanden.")
    
    # c) Excel filtern
    filtered = load_and_filter_schedule(schedule_xlsx)
    filtered.to_excel(OUT_FILTERED_XLSX, index=False)

    # d) Hallenverzeichnis scrapen + exportieren
    halls_df = scrape_halls_table()
    halls_df.to_excel(OUT_HALLS_XLSX, index=False)

    # e) Merge + exportieren
    merged = merge_schedule_with_halls(filtered, halls_df)
    merged.to_excel(OUT_MERGED_XLSX, index=False)

    print("Done.")
    print(f"- Gefilterter Spielplan: {OUT_FILTERED_XLSX}")
    print(f"- Hallenverzeichnis:    {OUT_HALLS_XLSX}")
    print(f"- Spielplan+Ort:        {OUT_MERGED_XLSX}")
