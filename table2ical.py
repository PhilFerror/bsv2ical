#!/usr/bin/env python3
"""
table2ical.py - Convert basketball schedule Excel file to iCal format

This script reads the filtered basketball schedule Excel file and converts it
to an iCal (.ics) format that can be imported into calendar applications.
"""

import pandas as pd
import os
from datetime import datetime, timedelta, timezone
import re

# -----------------------------
# 1) Shared Configuration
# -----------------------------
from run import (
    TARGET_LEAGUE, TARGET_TEAM,
    OUT_MERGED_XLSX, OUT_ICAL,
    CALENDAR_NAME, CALENDAR_DESCRIPTION,
    ICAL_TEMPLATE_TYPE, TEAM_COACH_NAME, TEAM_PLAYERS, TEAM_MEETING_TIME_OFFSET,
    ICAL_TIMEZONE, ICAL_USE_LOCAL_TIME
)

# Input file (from shared configuration)
INPUT_XLSX = OUT_MERGED_XLSX

# Output iCal file (from shared configuration)
OUTPUT_ICAL = OUT_ICAL

# -----------------------------
# 1) iCal Template System
# -----------------------------

## AUFSTELLUNG ✅
# {players}

def get_ical_template():
    """
    Get the appropriate iCal template based on configuration.
    
    Returns:
        str: Template string with placeholders
    """
    if ICAL_TEMPLATE_TYPE == "team":
        return """Hallihallo,
unser nächstes Saisonspiel (#{game_number}) - {game_type} steht an⛹🏼‍♂️:

# Spiel {league}, {day_name}, den {day_month}

## TREFFPUNKT ⏰ 
{meeting_time} Uhr Spielhalle

## SPIELHALLE 🏟️
*{hall_code}*- {hall_address}

## GEGNER 🆚
{opponent_team}

## SPIELBEGINN 🏀 
{game_time} Uhr

⚠️ _Sollte bereits wer wissen, dass er nicht kann, bitte Info *als Privatnachricht* an mich

## TRIKOTS 🎽
• Bitte eigene Hose mitbringen, wer hat gerne schwarze HOSE. 
• ⁠Shirt, Pullover oder Trainingsjacke zum Überziehen bzw Aufwärmen. 
• ⁠Trikots bringe ich mit.

## Mitbringen
• Trinkflasche nicht vergessen! und 
• ⁠gerne einen eigenen Ball zum Aufwärmen.

VG,
{coach_name}

Bei Fragen gerne melden."""
    else:
        # Basic template
        return """🏀 Basketball {game_type}

Liga: {league}
Datum: {day_name}, {day_month}
Zeit: {game_time} Uhr
Halle: {hall_code} - {hall_address}
Gegner: {opponent_team}

Treffpunkt: {meeting_time} Uhr Spielhalle

{coach_name}"""

def format_game_template(dt_start, dt_end, home_team, away_team, hall, hall_address, game_number=1):
    """
    Format the iCal template with dynamic values.
    
    Args:
        dt_start (datetime): Game start time
        dt_end (datetime): Game end time
        home_team (str): Home team name
        away_team (str): Away team name
        hall (str): Hall code
        hall_address (str): Hall address
        game_number (int): Game number in season
        
    Returns:
        str: Formatted template
    """
    # Determine game type
    is_home = TARGET_TEAM.upper() in home_team.upper()
    game_type = "HEIMSPIEL" if is_home else "AUSWÄRTSSPIEL"
    opponent_team = away_team if is_home else home_team
    
    # Format times
    game_time = dt_start.strftime("%H:%M")
    meeting_time_dt = dt_start - timedelta(minutes=TEAM_MEETING_TIME_OFFSET)
    meeting_time = meeting_time_dt.strftime("%H:%M")
    
    # Format date with German day names
    german_days = {
        'Monday': 'Montag',
        'Tuesday': 'Dienstag', 
        'Wednesday': 'Mittwoch',
        'Thursday': 'Donnerstag',
        'Friday': 'Freitag',
        'Saturday': 'Samstag',
        'Sunday': 'Sonntag'
    }
    
    english_day = dt_start.strftime("%A")
    day_name = german_days.get(english_day, english_day)
    day_month = dt_start.strftime("%d.%m")  # Day and month
    
    # Get template and format it
    template = get_ical_template()
    
    formatted = template.format(
        game_number=game_number,
        game_type=game_type,
        league=TARGET_LEAGUE,
        day_name=day_name,
        day_month=day_month,
        meeting_time=meeting_time,
        hall_code=hall,
        hall_address=hall_address,
        opponent_team=opponent_team,
        game_time=game_time,
        players=TEAM_PLAYERS,
        coach_name=TEAM_COACH_NAME
    )
    
    return formatted

# -----------------------------
# 2) Excel file reading function
# -----------------------------

def read_schedule_excel(file_path=INPUT_XLSX):
    """
    Read the basketball schedule Excel file and return a DataFrame.
    
    Args:
        file_path (str): Path to the Excel file
        
    Returns:
        pd.DataFrame: Schedule data with columns: DATUM, ZEIT, HALLE, HEIM, GAST, ADRESSE, PLZ, ORT
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Excel file not found: {file_path}")
        
        print(f"Reading Excel file: {file_path}")
        df = pd.read_excel(file_path)
        
        # Display basic info about the data
        print(f"Loaded {len(df)} games from Excel file")
        print(f"Columns: {list(df.columns)}")
        
        # Show first few rows
        if len(df) > 0:
            print("\nFirst 3 games:")
            print(df.head(3).to_string(index=False))
        
        return df
        
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None

# -----------------------------
# 2) Date/Time parsing functions
# -----------------------------

def parse_date_time(date_str, time_str):
    """
    Parse date and time strings and return a datetime object.
    
    Args:
        date_str (str): Date string (e.g., "2024-10-15" or "15.10.2024")
        time_str (str): Time string (e.g., "19:30" or "19:30:00")
        
    Returns:
        datetime: Combined datetime object
    """
    try:
        # Parse date - handle different formats
        if isinstance(date_str, str):
            # Try different date formats
            date_formats = ["%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"]
            parsed_date = None
            
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_str, fmt).date()
                    break
                except ValueError:
                    continue
            
            if parsed_date is None:
                # If it's already a datetime object
                if hasattr(date_str, 'date'):
                    parsed_date = date_str.date()
                else:
                    raise ValueError(f"Could not parse date: {date_str}")
        else:
            # Handle pandas datetime
            parsed_date = date_str.date() if hasattr(date_str, 'date') else date_str
        
        # Parse time
        if isinstance(time_str, str):
            # Remove seconds if present
            time_str = time_str.split(':')
            if len(time_str) >= 2:
                hour = int(time_str[0])
                minute = int(time_str[1])
            else:
                hour = 0
                minute = 0
        else:
            # Handle time objects
            if hasattr(time_str, 'hour'):
                hour = time_str.hour
                minute = time_str.minute
            else:
                hour = 0
                minute = 0
        
        # Combine date and time
        dt = datetime.combine(parsed_date, datetime.min.time().replace(hour=hour, minute=minute))
        return dt
        
    except Exception as e:
        print(f"Error parsing date/time: {date_str}, {time_str} - {e}")
        return None

def format_datetime_ical(dt):
    """
    Format datetime object for iCal format with proper timezone handling.
    
    Args:
        dt (datetime): Datetime object (assumed to be in local time)
        
    Returns:
        str: Formatted datetime string for iCal
    """
    if dt is None:
        return None
    
    if ICAL_USE_LOCAL_TIME:
        # Use local time without timezone info (floating time)
        # This is appropriate for events that happen at the same local time regardless of timezone
        return dt.strftime("%Y%m%dT%H%M%S")
    else:
        # Convert to UTC and format with Z suffix
        # This requires proper timezone conversion
        try:
            import pytz
            # Get the configured timezone
            tz = pytz.timezone(ICAL_TIMEZONE)
            # Localize the datetime to the configured timezone
            dt_localized = tz.localize(dt)
            # Convert to UTC
            dt_utc = dt_localized.astimezone(pytz.UTC)
            return dt_utc.strftime("%Y%m%dT%H%M%SZ")
        except ImportError:
            print("Warning: pytz not available, using local time without timezone conversion")
            return dt.strftime("%Y%m%dT%H%M%S")
        except Exception as e:
            print(f"Warning: Timezone conversion failed: {e}, using local time")
            return dt.strftime("%Y%m%dT%H%M%S")

# -----------------------------
# 3) iCal conversion function
# -----------------------------

def create_ical_event(dt_start, dt_end, summary, description, location):
    """
    Create a single iCal event entry.
    
    Args:
        dt_start (datetime): Event start time
        dt_end (datetime): Event end time
        summary (str): Event title
        description (str): Event description
        location (str): Event location
        
    Returns:
        str: iCal event entry
    """
    # Generate stable unique ID based on game details (not content that might change)
    # Format: basketball-{date}-{time}-{home_team}-{away_team}@{team}.local
    # This ensures same game always gets same UID, even if description changes
    
    # Extract team names from summary for stable UID
    teams = summary.replace("🏀 ", "").replace("Heimspiel: ", "").replace("Auswärtsspiel: ", "").split(" vs ")
    if len(teams) == 2:
        home_team = teams[0].strip()
        away_team = teams[1].strip()
        # Create stable identifier from game details
        game_id = f"{dt_start.strftime('%Y%m%d')}-{dt_start.strftime('%H%M')}-{home_team}-{away_team}"
    else:
        # Fallback to date/time if team parsing fails
        game_id = f"{dt_start.strftime('%Y%m%d')}-{dt_start.strftime('%H%M')}"
    
    uid = f"basketball-{game_id}@{TARGET_TEAM.lower()}.local"
    
    # Format times
    dtstart = format_datetime_ical(dt_start)
    dtend = format_datetime_ical(dt_end)
    
    # Escape special characters for iCal
    def escape_ical_text(text):
        if text is None:
            return ""
        text = str(text)
        text = text.replace("\\", "\\\\")
        text = text.replace(";", "\\;")
        text = text.replace(",", "\\,")
        text = text.replace("\n", "\\n")
        return text
    
    # Generate timestamp for last modification
    now = datetime.now()
    dtstamp = now.strftime("%Y%m%dT%H%M%SZ")
    
    event = f"""BEGIN:VEVENT
UID:{uid}
DTSTART:{dtstart}
DTEND:{dtend}
DTSTAMP:{dtstamp}
SUMMARY:{escape_ical_text(summary)}
DESCRIPTION:{escape_ical_text(description)}
LOCATION:{escape_ical_text(location)}
STATUS:CONFIRMED
TRANSP:OPAQUE
SEQUENCE:0
END:VEVENT"""
    
    return event

def convert_to_ical(df, output_file=OUTPUT_ICAL):
    """
    Convert DataFrame to iCal format and save to file.
    
    Args:
        df (pd.DataFrame): Schedule data
        output_file (str): Output iCal file path
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if df is None or len(df) == 0:
            print("No data to convert")
            return False
        
        print(f"Converting {len(df)} games to iCal format...")
        
        # Create iCal header with timezone information
        ical_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//BSV Basketball//Schedule Converter//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:{CALENDAR_NAME}
X-WR-CALDESC:{CALENDAR_DESCRIPTION}
X-WR-TIMEZONE:{ICAL_TIMEZONE}
"""
        
        # Process each game
        events = []
        for index, row in df.iterrows():
            try:
                # Parse date and time
                dt_start = parse_date_time(row['DATUM'], row['ZEIT'])
                if dt_start is None:
                    print(f"Skipping game {index + 1}: Could not parse date/time")
                    continue
                
                # Calculate end time (assume 1.5 hours duration)
                dt_end = dt_start + timedelta(hours=1, minutes=30)
                
                # Create event details
                home_team = str(row.get('HEIM', ''))
                away_team = str(row.get('GAST', ''))
                hall = str(row.get('HALLE', ''))
                
                # Determine if this is a home or away game
                is_home = TARGET_TEAM.upper() in home_team.upper()
                opponent = away_team if is_home else home_team
                game_type = "Heimspiel" if is_home else "Auswärtsspiel"
                
                # Create summary
                summary = f"🏀 {game_type}: {TARGET_TEAM} vs {opponent}"
                
                # Create description using template
                hall_address = ""
                if 'Adresse' in row and pd.notna(row['Adresse']):
                    hall_address = str(row['Adresse']).strip()
                elif 'PLZ' in row and pd.notna(row['PLZ']) and 'Ort' in row and pd.notna(row['Ort']):
                    plz = str(row['PLZ']).strip()
                    ort = str(row['Ort']).strip()
                    hall_address = f"{plz} {ort}"
                
                # Use template for description
                description = format_game_template(
                    dt_start, dt_end, home_team, away_team, 
                    hall, hall_address, game_number=index + 1
                )
                
                # Create location
                location_parts = []
                if hall:
                    location_parts.append(hall)
                
                # Add address if available
                if 'ADRESSE' in row and pd.notna(row['ADRESSE']):
                    location_parts.append(str(row['ADRESSE']))
                
                if 'PLZ' in row and pd.notna(row['PLZ']):
                    plz = str(row['PLZ']).strip()
                    if plz:
                        location_parts.append(plz)
                
                if 'ORT' in row and pd.notna(row['ORT']):
                    ort = str(row['ORT']).strip()
                    if ort:
                        location_parts.append(ort)
                
                location = ", ".join(location_parts) if location_parts else hall
                
                # Create iCal event
                event = create_ical_event(dt_start, dt_end, summary, description, location)
                events.append(event)
                
                print(f"✓ Game {index + 1}: {summary} - {dt_start.strftime('%d.%m.%Y %H:%M')}")
                
            except Exception as e:
                print(f"Error processing game {index + 1}: {e}")
                continue
        
        # Add all events to iCal content
        ical_content += "\n".join(events)
        
        # Close iCal
        ical_content += "\nEND:VCALENDAR"
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(ical_content)
        
        print(f"\n✅ Successfully created iCal file: {output_file}")
        print(f"📅 {len(events)} events exported")
        
        return True
        
    except Exception as e:
        print(f"Error converting to iCal: {e}")
        return False

# -----------------------------
# 4) Main execution
# -----------------------------

def main():
    """Main function to run the conversion process."""
    print("🏀 Basketball Schedule to iCal Converter")
    print("=" * 50)
    
    # Read Excel file
    df = read_schedule_excel()
    if df is None:
        print("❌ Failed to read Excel file")
        return
    
    # Convert to iCal
    success = convert_to_ical(df)
    if success:
        print(f"\n🎉 Conversion completed successfully!")
        print(f"📁 iCal file saved as: {OUTPUT_ICAL}")
        print(f"📱 You can now import this file into your calendar application")
    else:
        print("❌ Conversion failed")

if __name__ == "__main__":
    main()
