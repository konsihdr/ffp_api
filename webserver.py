from datetime import datetime, timedelta, timezone

from icalendar import Calendar
import requests
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# URL des öffentlichen Google Kalenders im iCal-Format (ICS)
CALENDAR_URL="https://calendar.google.com/calendar/ical/46h88cspd4jsh261dgggqgoevk%40group.calendar.google.com/public/basic.ics"

# Funktion zum Abrufen und Verarbeiten der Ereignisse im ICS-Format
def get_calendar_events():
    response = requests.get(CALENDAR_URL)
    if response.status_code == 200:
        ics_content = response.content
        calendar = Calendar.from_ical(ics_content)

        events = []
        for event in calendar.walk('vevent'):
            event_data = {
                'summary': event.get('summary').to_ical().decode('utf-8'),
                'start': event.get('dtstart').dt.isoformat(),
                'end': event.get('dtend').dt.isoformat()
            }
            events.append(event_data)

        return events
    else:
        return None

# Funktion zum Abrufen des nächsten Jugendübung-Events
def get_next_youth_training_event():
    events = get_calendar_events()
    if events is not None:
        germany_tz = timezone(timedelta(hours=2))  # UTC+2 für Deutschland
        now = datetime.now(germany_tz)
        youth_events = [event for event in events if 'Jugenduebung' in event['summary']]

        if youth_events:
            next_youth_event = min(youth_events, key=lambda event: datetime.fromisoformat(event['start']).replace(tzinfo=germany_tz) if datetime.fromisoformat(event['start']).replace(tzinfo=germany_tz) >= now else datetime.max.replace(tzinfo=germany_tz))
            return next_youth_event
        else:
            return None
    else:
        return None
    
# Funktion zum Abrufen des nächsten Events
def get_next_event():
    events = get_calendar_events()
    if events is not None:
        germany_tz = timezone(timedelta(hours=2))  # UTC+2 für Deutschland
        now = datetime.now(germany_tz)
        next_events = [event for event in events]

        if next_events:
            next_event = min(next_events, key=lambda event: datetime.fromisoformat(event['start']).replace(tzinfo=germany_tz) if datetime.fromisoformat(event['start']).replace(tzinfo=germany_tz) >= now else datetime.max.replace(tzinfo=germany_tz))
            return next_event
        else:
            return None
    else:
        return None

# Definiere eine API-Routes
@app.route('/api/all', methods=['GET'])
def all_events():
    events = get_calendar_events()

    if events is not None:
        return jsonify(events)
    else:
        return jsonify({'error': 'Failed to fetch calendar events'})

@app.route('/api/ne', methods=['GET'])
def next_event():
    next_event = get_next_event()

    if next_event is not None:
        return jsonify(next_event)
    else:
        return jsonify({'error': 'Failed to fetch calendar events'})
    
@app.route('/api/nj', methods=['GET'])
def next_youth_event():
    next_event = get_next_youth_training_event()

    if next_event is not None:
        return jsonify(next_event)
    else:
        return jsonify({'error': 'No upcoming youth events found'})
    
@app.route('/api/ping', methods=['GET'])
def ping():
    return "Pong", 200, {"Access-Control-Allow-Origin": "*"}

if __name__ == '__main__':
    app.run(debug=True)
