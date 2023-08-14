from flask import Flask, jsonify, request
from functools import wraps
import requests
import icalendar
from io import BytesIO
from datetime import datetime, timezone, timedelta
import os

app = Flask(__name__)

# URL des öffentlichen Google Kalenders im iCal-Format (ICS)
CALENDAR_URL = os.environ['CALENDAR_URL']
API_KEY = os.environ['API_KEY']

# Benutzerdefinierter Dekorator zur Überprüfung des API-Schlüssels
def require_api_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        provided_key = request.headers.get('x-api-key')
        if provided_key == API_KEY:
            return func(*args, **kwargs)
        else:
            return jsonify({'error': 'Invalid API key'}), 401
    return wrapper

# Funktion zum Abrufen und Verarbeiten der Ereignisse im ICS-Format
def get_calendar_events():
    response = requests.get(CALENDAR_URL)
    if response.status_code == 200:
        ics_content = response.content
        calendar = icalendar.Calendar.from_ical(ics_content)

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

# Definiere eine API-Routes
@app.route('/api/all-events', methods=['GET'])
def all_events():
    events = get_calendar_events()

    if events is not None:
        return jsonify(events)
    else:
        return jsonify({'error': 'Failed to fetch calendar events'})

@app.route('/api/next-event', methods=['GET'])
def next_event():
    events = get_calendar_events()

    if events is not None:
        return jsonify(events)
    else:
        return jsonify({'error': 'Failed to fetch calendar events'})
    
@app.route('/api/next-ju', methods=['GET'])
def next_youth_event():
    next_event = get_next_youth_training_event()

    if next_event is not None:
        return jsonify(next_event)
    else:
        return jsonify({'error': 'No upcoming youth events found'})

if __name__ == '__main__':
    app.run(debug=True)
