from flask import Flask, request, jsonify
from datetime import datetime
from pytz import timezone
import sqlite3
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Database setup
def init_db():
    conn = sqlite3.connect('meal_ticketing.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS meal_tickets (
                    email TEXT,
                    date TEXT,
                    meal_count INTEGER
                 )''')
    conn.commit()
    populate_sample_data()
    conn.close()

# Helper function to check if user exists and has taken dinner today
def check_user(email, current_date):
    conn = sqlite3.connect('meal_ticketing.db')
    c = conn.cursor()
    c.execute('SELECT * FROM meal_tickets WHERE email=? AND date=?', (email, current_date))
    result = c.fetchall()
    conn.close()
    return result

# Function to populate sample data
def populate_sample_data():
    sample_users = [
        ('john.doe@example.com', '2024-11-09', 1),
        ('jane.smith@example.com', '2024-11-09', 0),
        ('mike.jones@example.com', '2024-11-08', 2),
        ('alice.brown@example.com', '2024-11-09', 0),
        ('bob.white@example.com', '2024-11-07', 1)
    ]
    conn = sqlite3.connect('meal_ticketing.db')
    c = conn.cursor()
    for user in sample_users:
        email, date, meal_count = user
        c.execute('SELECT * FROM meal_tickets WHERE email=? AND date=?', (email, date))
        if not c.fetchall():
            c.execute('INSERT INTO meal_tickets (email, date, meal_count) VALUES (?, ?, ?)', (email, date, meal_count))
    conn.commit()
    conn.close()

@app.route('/meal-ticket', methods=['POST'])
def meal_ticket():
    data = request.json
    email = data.get('email')
    qr_code_data = data.get('qrCodeData')
    current_time = data.get('time')

    #return jsonify({"message": "Time is required."}), 200
    
    # Validate time format
    if not current_time:
        return jsonify({"message": "Time is required."}), 400
    
    try:
        current_datetime = datetime.fromisoformat(current_time)
    except ValueError:
        return jsonify({"message": "Invalid time format. Expected format: YYYY-MM-DDTHH:MM:SS"}), 400

    current_hour = current_datetime.hour
    if current_hour < 2 or current_hour >= 12:
        return jsonify({"message": "This system accepts meal tickets only between 1 AM and 12 PM."}), 400

    current_date = current_datetime.strftime('%Y-%m-%d')
    if not email:
        return jsonify({"message": "Email is required."}), 400

    existing_meal = check_user(email, current_date)
    if existing_meal:
        meal_count = existing_meal[0][2]
        if meal_count >= 2:
            return jsonify({"message": "You have already collected dinner twice today. Please try again tomorrow."}), 400
        else:
            conn = sqlite3.connect('meal_ticketing.db')
            c = conn.cursor()
            c.execute('UPDATE meal_tickets SET meal_count = meal_count + 1 WHERE email=? AND date=?', (email, current_date))
            conn.commit()
            conn.close()
            return jsonify({"message": "Here is your dinner! Enjoy!"}), 200
    else:
        conn = sqlite3.connect('meal_ticketing.db')
        c = conn.cursor()
        c.execute('INSERT INTO meal_tickets (email, date, meal_count) VALUES (?, ?, ?)', (email, current_date, 1))
        conn.commit()
        conn.close()
        return jsonify({"message": "Here is your dinner! Enjoy!"}), 200

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
