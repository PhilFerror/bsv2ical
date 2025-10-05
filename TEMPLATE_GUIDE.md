# 📝 iCal Template System Guide

## Overview

The iCal template system allows you to customize how your basketball game information appears in calendar events. It uses your team communication templates with dynamic values automatically filled in.

## Template Types

### 1. Team Template (Detailed)
**Configuration**: `ICAL_TEMPLATE_TYPE = "team"`

**Features**:
- Full team communication style
- Includes all team information (players, coach, equipment)
- Meeting time calculation
- German day names
- Complete game details

**Example Output**:
```
Hallihallo,
unser nächstes Saisonspiel und 3. HEIMSPIEL steht an⛹🏼‍♂️:

# Spiel M10C, Sonntag, den 05.10

## TREFFPUNKT ⏰ 
13:45 Uhr Spielhalle

## SPIELHALLE 🏟️
*HBV-HEST*- ReBBZ-Bildungsabteilung Standort Heidstücken, Heidstücken 33, 22179 Hamburg

## GEGNER 🆚
HOEP

## SPIELBEGINN 🏀 
14:30 Uhr

## AUFSTELLUNG ✅
Player1 Player2 Player3

⚠️ _Sollte bereits wer wissen, dass er nicht kann, bitte Info *als Privatnachricht* an mich

## TRIKOTS 🎽
• Bitte eigene Hose mitbringen, wer hat gerne schwarze HOSE. 
• ⁠Shirt, Pullover oder Trainingsjacke zum Überziehen bzw Aufwärmen. 
• ⁠Trikots bringe ich mit.

## Kampfgericht
🚨 Wir stellen das Kampfgericht, es werden 2 Eltern benötigt für das Anschreiben und die Stoppuhr 🚨 

## Mitbringen
• Trinkflasche nicht vergessen! und 
• ⁠gerne einen eigenen Ball zum Aufwärmen.

VG,
Super Trainer

Bei Fragen gerne melden.
```

### 2. Basic Template (Simple)
**Configuration**: `ICAL_TEMPLATE_TYPE = "basic"`

**Features**:
- Simple, clean format
- Essential information only
- Compact design
- Easy to read

**Example Output**:
```
🏀 Basketball HEIMSPIEL

Liga: M10C
Datum: Sonntag, 05.10
Zeit: 14:30 Uhr
Halle: HBV-HEST - ReBBZ-Bildungsabteilung Standort Heidstücken, Heidstücken 33, 22179 Hamburg
Gegner: HOEP

Treffpunkt: 13:45 Uhr Spielhalle
```

## Configuration Options

### Template Selection
```python
# In run.py
ICAL_TEMPLATE_TYPE = "team"  # or "basic"
```

### Team Information
```python
# Team-specific information for templates
TEAM_COACH_NAME = "Super Trainer"
TEAM_PLAYERS = "Player1 Player2"
TEAM_MEETING_TIME_OFFSET = 45  # Minutes before game start for team meeting
```

## Dynamic Values

The following values are automatically filled in from your schedule data:

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{game_number}` | Sequential game number | `3` |
| `{game_type}` | HEIMSPIEL or AUSWÄRTSSPIEL | `HEIMSPIEL` |
| `{league}` | League name | `M10C` |
| `{day_name}` | German day name | `Sonntag` |
| `{day_month}` | Day and month | `05.10` |
| `{meeting_time}` | Team meeting time | `13:45` |
| `{hall_code}` | Hall code | `HBV-HEST` |
| `{hall_address}` | Full hall address | `ReBBZ-Bildungsabteilung Standort Heidstücken, Heidstücken 33, 22179 Hamburg` |
| `{opponent_team}` | Opponent team name | `HOEP` |
| `{game_time}` | Game start time | `14:30` |
| `{players}` | Team player list | `Player1, Player2, Player3, ...` |
| `{coach_name}` | Coach name | `Super Trainer` |

## Customizing Templates

### Method 1: Edit Configuration (Recommended)
Modify the template configuration in `run.py`:

```python
# Change template type
ICAL_TEMPLATE_TYPE = "basic"  # Switch to basic template

# Update team information
TEAM_COACH_NAME = "Your Coach Name"
TEAM_PLAYERS = "Player1, Player2, Player3, ..."
TEAM_MEETING_TIME_OFFSET = 30  # Change meeting time to 30 minutes before
```

### Method 2: Modify Template Code (Advanced)
Edit the template strings in `table2ical.py`:

```python
def get_ical_template():
    if ICAL_TEMPLATE_TYPE == "team":
        return """Your custom template here...
        with {placeholders} for dynamic values"""
    else:
        return """Your basic template here..."""
```

## Template Examples

### Custom Team Template
```python
# In table2ical.py, modify the team template:
return """🏀 BASKETBALL GAME ALERT! 🏀

Game #{game_number}: {game_type}
League: {league}
Date: {day_name}, {day_month}
Time: {game_time} Uhr

📍 Location: {hall_code} - {hall_address}
🆚 Opponent: {opponent_team}

⏰ Team Meeting: {meeting_time} Uhr at the hall

👥 Players: {players}

Coach: {coach_name}
"""
```

### Custom Basic Template
```python
# In table2ical.py, modify the basic template:
return """{game_type} vs {opponent_team}
{day_name}, {day_month} at {game_time} Uhr
{hall_code} - {hall_address}
Meeting: {meeting_time} Uhr
{coach_name}"""
```

## Best Practices

### 1. Keep Templates Readable
- Use clear section headers
- Include emojis for visual appeal
- Keep important information at the top

### 2. Include Essential Information
- Game time and date
- Location and address
- Opponent team
- Meeting time
- Contact information

### 3. Consider Your Audience
- **Team Template**: For team members and parents
- **Basic Template**: For general calendar viewing

### 4. Test Your Templates
1. Generate a test calendar file
2. Import into your calendar app
3. Check how the description appears
4. Adjust formatting as needed

## Troubleshooting

### Problem: Template Not Updating
**Solution**: 
1. Check `ICAL_TEMPLATE_TYPE` in `run.py`
2. Regenerate the calendar file
3. Re-import into your calendar app

### Problem: German Day Names Not Working
**Solution**: 
The system automatically converts English day names to German. If you need other languages, modify the `german_days` dictionary in `table2ical.py`.

### Problem: Meeting Time Calculation Wrong
**Solution**: 
Adjust `TEAM_MEETING_TIME_OFFSET` in `run.py` to change how many minutes before the game the team should meet.

### Problem: Template Too Long
**Solution**: 
1. Switch to `ICAL_TEMPLATE_TYPE = "basic"`
2. Or modify the team template to be shorter
3. Remove unnecessary sections

## Advanced Customization

### Adding New Placeholders
1. Add new placeholder to template: `{new_value}`
2. Add value to `format_game_template()` function
3. Update this documentation

### Multiple Template Options
You can add more template types by:
1. Adding new conditions in `get_ical_template()`
2. Adding new configuration options in `run.py`
3. Creating new template strings

### Conditional Content
You can add conditional content based on game type:

```python
# In format_game_template()
if is_home:
    home_specific_info = "We're playing at home!"
else:
    home_specific_info = "Away game - check travel time!"

# Add to template
formatted = template.format(
    # ... other values ...
    home_info=home_specific_info
)
```

---

**Remember**: The template system is designed to be flexible and easy to customize. Start with the provided templates and modify them to match your team's communication style! 🏀📅
