#!/usr/bin/env python3
"""
run.py - Main execution script for basketball schedule processing

This script contains the shared configuration values and main execution function
that runs both filter.py and table2ical.py in sequence.
"""

import subprocess
import sys
import os

# -----------------------------
# Filter-Konfiguration
# -----------------------------

# Liga und Team die gefiltert werden sollen
TARGET_LEAGUE = "M10C"  # Liga die gefiltert werden sollen
TARGET_TEAM = "BSV"     # Team das gefiltert werden soll (HEIM oder GAST)

# -----------------------------
# Datei-Konfiguration
# -----------------------------

# Input-Dateien
SCHEDULE_XLSM = "Gesamtspielplan-2025-26_20250918.xlsm"  # <- your local XLSM file
SCHEDULE_XLSX = "Gesamtspielplan-2025-26_20250918.xlsx"  # <- converted XLSX file
SCHEDULE_SHEET = "Gesamtspielplan"
HALLS_URL = "https://hamburg-basket.de/hallen/"
SCHEDULE_URL = "https://hamburg-basket.de/gesamtspielplan/"
HALL_OVERRIDES_JSON = "hall_overrides.json"

# Output-Dateien (werden basierend auf Konfiguration generiert)
OUT_FILTERED_XLSX = f"Spiele_{TARGET_LEAGUE}_{TARGET_TEAM}.xlsx"
OUT_HALLS_XLSX = "Hallenverzeichnis_HBV_2025_2026.xlsx"
OUT_MERGED_XLSX = f"Spiele_{TARGET_LEAGUE}_{TARGET_TEAM}_mit_Ort.xlsx"
OUT_ICAL = f"Spiele_{TARGET_LEAGUE}_{TARGET_TEAM}.ics"

# -----------------------------
# Automatische Downloads
# -----------------------------

AUTO_DOWNLOAD_SCHEDULE = True  # Automatisch neueste Datei von Website laden
# Setzen Sie AUTO_DOWNLOAD_SCHEDULE = False um nur lokale Dateien zu verwenden

# -----------------------------
# Kalender-Konfiguration
# -----------------------------

CALENDAR_NAME = f"{TARGET_TEAM} Basketball {TARGET_LEAGUE}"
CALENDAR_DESCRIPTION = f"Basketball Spiele - Liga {TARGET_LEAGUE} - Team {TARGET_TEAM}"

# -----------------------------
# Hall Scraping Resilience Configuration
# -----------------------------

# Configurable regex patterns for hall code detection
HALL_CODE_PATTERNS = [
    r'^[A-ZÄÖÜ]{2,}\s?[0-9]?$',  # Primary: German umlauts + optional space + optional number
    r'^[A-Z]{2,}[0-9]?$',        # Fallback: No umlauts
    r'^[A-ZÄÖÜ]{2,}$',           # Fallback: No numbers
    r'^[A-Z]{2,}$',              # Fallback: Basic pattern
]

# Reference hall patterns (configurable)
REFERENCE_PATTERNS = [
    r'^Siehe\s+([A-Z0-9]+)$',      # "Siehe KGSE1"
    r'^Siehe\s+([A-Z0-9]+)\s*$',   # "Siehe KGSE1 " (with trailing space)
    r'^siehe\s+([A-Z0-9]+)$',      # "siehe KGSE1" (lowercase)
    r'^siehe\s+([A-Z0-9]+)\s*$',   # "siehe KGSE1 " (lowercase with trailing space)
    r'^Vgl\.\s+([A-Z0-9]+)$',      # "Vgl. KGSE1" (Vergleich/Compare)
    r'^Vgl\.\s+([A-Z0-9]+)\s*$',   # "Vgl. KGSE1 " (with trailing space)
    r'^See\s+([A-Z0-9]+)$',        # "See KGSE1" (English fallback)
    r'^see\s+([A-Z0-9]+)$',        # "see KGSE1" (English lowercase)
]

# Address detection patterns
ADDRESS_PATTERNS = [
    r'\b\d{5}\b',                  # 5-digit postal code
    r'HH\b',                       # Hamburg abbreviation
    r'Hamburg',                    # Full Hamburg name
    r'\d{4}\s+[A-Za-z]',          # 4-digit postal code (some areas)
]

# -----------------------------
# iCal Template Configuration
# -----------------------------

# Template selection: 'basic' or 'team'
ICAL_TEMPLATE_TYPE = "team"  # Use "team" for detailed template, "basic" for simple template

# Team-specific information for templates
TEAM_COACH_NAME = ""
TEAM_PLAYERS = "tbd"
TEAM_MEETING_TIME_OFFSET = 45  # Minutes before game start for team meeting

# Timezone configuration for iCal
ICAL_TIMEZONE = "Europe/Berlin"  # German timezone (CET/CEST)
ICAL_USE_LOCAL_TIME = True  # Set to False to use UTC

# -----------------------------
# Main Execution Function
# -----------------------------

def run_script(script_name):
    """
    Run a Python script and return the result.
    
    Args:
        script_name (str): Name of the script to run
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"\n{'='*60}")
        print(f"🚀 Running {script_name}...")
        print(f"{'='*60}")
        
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=False, 
                              text=True, 
                              cwd=os.path.dirname(os.path.abspath(__file__)))
        
        if result.returncode == 0:
            print(f"\n✅ {script_name} completed successfully!")
            return True
        else:
            print(f"\n❌ {script_name} failed with exit code {result.returncode}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error running {script_name}: {e}")
        return False

def main():
    """
    Main execution function that runs both scripts in sequence.
    """
    print("🏀 Basketball Schedule Processing Pipeline")
    print("=" * 60)
    print(f"📋 Configuration:")
    print(f"   League: {TARGET_LEAGUE}")
    print(f"   Team: {TARGET_TEAM}")
    print(f"   Auto Download: {AUTO_DOWNLOAD_SCHEDULE}")
    print("=" * 60)
    
    # Step 1: Run filter.py
    print(f"\n📊 Step 1: Filtering schedule and processing hall data...")
    filter_success = run_script("filter.py")
    
    if not filter_success:
        print("\n❌ Pipeline stopped: filter.py failed")
        return False
    
    # Step 2: Run table2ical.py
    print(f"\n📅 Step 2: Converting to calendar format...")
    ical_success = run_script("table2ical.py")
    
    if not ical_success:
        print("\n❌ Pipeline stopped: table2ical.py failed")
        return False
    
    # Success summary
    print(f"\n{'='*60}")
    print("🎉 Pipeline completed successfully!")
    print(f"{'='*60}")
    print(f"📁 Generated files:")
    print(f"   📊 {OUT_FILTERED_XLSX}")
    print(f"   🏢 {OUT_HALLS_XLSX}")
    print(f"   📋 {OUT_MERGED_XLSX}")
    print(f"   📅 {OUT_ICAL}")
    print(f"\n📱 You can now import {OUT_ICAL} into your calendar application!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
