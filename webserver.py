from datetime import datetime, timedelta, timezone

from icalendar import Calendar
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from requests_cache import CachedSession

from pymongo import MongoClient
import os 

app = Flask(__name__)
CORS(app)

# CachedSession mit einer SQLite-Datenbank als Cache
session = CachedSession('ffp_api', backend='sqlite', expire_after=24*60*60)  # Gültigkeitsdauer: 24 Stunden

# URL des öffentlichen Google Kalenders im iCal-Format (ICS)
CALENDAR_URL="https://calendar.google.com/calendar/ical/74ba620d6f97d3d076e54247195ee2b2c927e257967c3d71c735e40d95dd8359%40group.calendar.google.com/private-c7ea8ddcff03ae10cb2593e1820e4d55/basic.ics"

# pymongo client setup
client = MongoClient(f"mongodb+srv://{os.environ['MONGO_USR']}:{os.environ['MONGO_PW']}@cluster0.4bhjk.mongodb.net/")

# Funktion zum Abrufen und Verarbeiten der Ereignisse im ICS-Format
def get_calendar_events():
    response = session.get(CALENDAR_URL)
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
    
# Funktion zum Abrufen der nächsten Events basierend auf der Anzahl
def get_next_events(c):
    events = get_calendar_events()
    if events is not None:
        germany_tz = timezone(timedelta(hours=2))  # UTC+2 für Deutschland
        now = datetime.now(germany_tz)
        next_events = [event for event in events if datetime.fromisoformat(event['start']).replace(tzinfo=germany_tz) >= now]


        if next_events:
            sorted_events = sorted(next_events, key=lambda event: datetime.fromisoformat(event['start']).replace(tzinfo=germany_tz) if datetime.fromisoformat(event['start']).replace(tzinfo=germany_tz) >= now else datetime.max.replace(tzinfo=germany_tz))
            return sorted_events[:c]
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
    count = int(request.args.get('c', 1))  # Standardwert: 1
    next_events = get_next_events(count)

    if len(next_events) == 1 :
        return jsonify(next_events[0])
    elif len(next_events) > 1:
        return jsonify(next_events)
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
    return jsonify({'msg': 'pong'})

# API routes for posts
@app.route('/api/posts/all', methods=['GET'])
def all_posts():
    db = client.ffp
    collection = db.posts
    try:
        posts = collection.find({}, {'alt': 1, 'caption': 1, 'url': 1, '_id': 0, 'displayUrl': 1, 'timestamp': 1}).sort([('timestamp', -1)]).limit(12)
        # Convert documents to list of dictionaries and exclude _id field
        posts_list = [{k: v for k, v in post.items() if k != '_id'} for post in posts]
        return jsonify(posts_list)
    except:
        return jsonify({'error': 'Failed to fetch posts'})

@app.route('/api/posts/latest', methods=['GET'])
def latest_posts():
    db = client.ffp
    collection = db.posts
    try:
        posts = collection.find({}, {'alt': 1, 'caption': 1, 'url': 1, '_id': 0, 'displayUrl': 1, 'timestamp': 1}).sort([('timestamp', -1)]).limit(1)
        # Convert documents to list of dictionaries and exclude _id field
        posts_list = [{k: v for k, v in post.items() if k != '_id'} for post in posts]
        return jsonify(posts_list[0])
    except:
        return jsonify({'error': 'Failed to fetch posts'})


if __name__ == '__main__':
    app.run(debug=True)
