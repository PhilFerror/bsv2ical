# 📅 iCal Update Guide

## How Calendar Updates Work

### **Understanding iCal Updates**

When you import an iCal file into your calendar application, each event gets a **unique identifier (UID)**. Calendar apps use this UID to determine whether to:
- ✅ **Update existing event** (same UID)
- ❌ **Create duplicate event** (different UID)

### **Our Improved UID System**

We've implemented a **stable UID generation** that ensures the same game always gets the same UID, even if details change.

#### **New UID Format:**
```
basketball-{YYYYMMDD}-{HHMM}-{HOME_TEAM}-{AWAY_TEAM}@{TEAM}.local
```

#### **Examples:**
- `basketball-20250920-1330-BSV-ETV@bsv.local`
- `basketball-20250927-1230-BSV-WINS@bsv.local`
- `basketball-20251005-1430-BSV-HOEP@bsv.local`

### **What This Means for Updates**

✅ **Same Game, Same UID**: The UID is based on date, time, and teams - not on changeable content like descriptions or locations.

✅ **Automatic Updates**: When you re-import the calendar file, existing events will be updated with new information.

✅ **No Duplicates**: You won't get duplicate events when re-importing.

## 📱 **How to Update Your Calendar**

### **Method 1: Re-import the File (Recommended)**

1. **Generate new calendar file**:
   ```bash
   python3 run.py
   ```

2. **Import the new file** into your calendar app:
   - **iPhone**: Settings → Calendar → Accounts → Add Account → Other → Add Subscribed Calendar
   - **Google Calendar**: Import & Export → Import → Select file
   - **Outlook**: File → Open & Export → Import/Export → Import an iCalendar file

3. **Calendar app will automatically**:
   - Update existing events with new information
   - Add any new games
   - Remove games that are no longer in the schedule

### **Method 2: Subscribe to Calendar (Advanced)**

For automatic updates, you can set up a web subscription:

1. **Host the .ics file** on a web server
2. **Subscribe to the URL** in your calendar app
3. **Calendar will check for updates** automatically

## 🔄 **Update Scenarios**

### **Scenario 1: Game Time Changes**
- **Before**: Game at 13:30
- **After**: Game moved to 14:00
- **Result**: ✅ Same UID, event time updated

### **Scenario 2: Venue Changes**
- **Before**: Game at "HBV-BREH2"
- **After**: Game moved to "HBV-HEST"
- **Result**: ✅ Same UID, location updated

### **Scenario 3: New Games Added**
- **Before**: 17 games in calendar
- **After**: 18 games in new file
- **Result**: ✅ 17 games updated, 1 new game added

### **Scenario 4: Games Cancelled**
- **Before**: 17 games in calendar
- **After**: 16 games in new file
- **Result**: ✅ 16 games updated, 1 game removed

## 🛠️ **Technical Details**

## 🕐 **Timezone Configuration**

### **Timezone Settings**

The system supports two timezone modes:

#### **Local Time Mode (Recommended)**
```python
ICAL_USE_LOCAL_TIME = True
ICAL_TIMEZONE = "Europe/Berlin"
```

**Result**: `DTSTART:20250920T133000` (no timezone suffix)
- Events appear at the correct local time regardless of your device's timezone
- Best for local events that don't change with timezone

#### **UTC Mode**
```python
ICAL_USE_LOCAL_TIME = False
ICAL_TIMEZONE = "Europe/Berlin"
```

**Result**: `DTSTART:20250920T113000Z` (UTC with Z suffix)
- Events are converted to UTC and display correctly across timezones
- Requires `pytz` library for proper timezone conversion

### **Calendar Header**
```ical
X-WR-TIMEZONE:Europe/Berlin
```
This tells calendar applications which timezone the events are in.

### **iCal Properties for Updates**

Our events include these properties for proper update handling:

```ical
BEGIN:VEVENT
UID:basketball-20250920-1330-BSV-ETV@bsv.local
DTSTART:20250920T133000Z
DTEND:20250920T150000Z
DTSTAMP:20251005T123532Z          # Last modification timestamp
SUMMARY:🏀 Auswärtsspiel: BSV vs ETV
DESCRIPTION:Basketball Auswärtsspiel\nLiga: M10C\nBSV vs ETV\nHalle: HBV-BREH2
LOCATION:HBV-BREH2, 22527
STATUS:CONFIRMED
TRANSP:OPAQUE
SEQUENCE:0                        # Update sequence number
END:VEVENT
```

### **Key Properties Explained**

- **UID**: Unique identifier (never changes for same game)
- **DTSTAMP**: When the event was last modified
- **SEQUENCE**: Update sequence number (increments with each update)
- **SUMMARY**: Event title (can change)
- **DESCRIPTION**: Event details (can change)
- **LOCATION**: Event location (can change)

## 🚨 **Troubleshooting**

### **Problem: Duplicate Events**
**Cause**: Calendar app doesn't recognize events as the same
**Solution**: 
1. Delete the old calendar
2. Import the new file
3. Or manually delete duplicate events

### **Problem: Events Not Updating**
**Cause**: Calendar app caching or sync issues
**Solution**:
1. Force refresh your calendar app
2. Check if calendar app supports iCal updates
3. Try re-importing the file

### **Problem: Missing Events**
**Cause**: Import failed or file corrupted
**Solution**:
1. Check if the .ics file was generated successfully
2. Try importing again
3. Check calendar app's import logs

## 📋 **Best Practices**

### **For Regular Updates**
1. **Run the script weekly** to get latest schedule changes
2. **Re-import the calendar file** after each run
3. **Keep the same file name** for consistency

### **For Team Changes**
1. **Update configuration** in `run.py`:
   ```python
   TARGET_LEAGUE = "W12A"  # New league
   TARGET_TEAM = "ETV"     # New team
   ```
2. **Generate new calendar** with different UIDs
3. **Import as separate calendar** or replace existing one

### **For Multiple Teams**
1. **Create separate calendar files** for each team
2. **Use different team names** in configuration
3. **Import each as separate calendar** in your app

## 🔧 **Advanced Configuration**

### **Custom UID Format**
You can modify the UID generation in `table2ical.py`:

```python
# Current format
uid = f"basketball-{game_id}@{TARGET_TEAM.lower()}.local"

# Custom format example
uid = f"hbv-{TARGET_LEAGUE.lower()}-{game_id}@hamburg-basket.de"
```

### **Update Frequency**
- **Manual**: Run script when needed
- **Automated**: Set up cron job or scheduled task
- **Web-based**: Host file on web server for automatic updates

## 📞 **Support**

If you encounter issues with calendar updates:

1. **Check the generated .ics file** - open it in a text editor to verify content
2. **Test with a simple calendar app** first (like Apple Calendar)
3. **Check your calendar app's documentation** for iCal import/update support
4. **Verify the UID format** matches what your calendar app expects

---

**Remember**: The key to successful updates is using the same UID for the same event. Our system ensures this happens automatically! 🏀📅
