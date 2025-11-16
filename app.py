from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import mysql.connector
import bcrypt
import os
from datetime import timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
CORS(app)

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'system',
    'database': 'computer_lab_inventory'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return jsonify({'success': True, 'message': 'Login successful'})
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'})
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/inventory')
def get_inventory():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM inventory ORDER BY date_added DESC")
    items = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Convert datetime objects to strings
    for item in items:
        if item['date_added']:
            item['date_added'] = item['date_added'].strftime('%Y-%m-%d %H:%M:%S')
    
    return jsonify(items)

@app.route('/inventory', methods=['POST'])
def add_item():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO inventory (item_name, item_type, serial_number, location, status, specifications)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (data['item_name'], data['item_type'], data['serial_number'], 
              data['location'], data['status'], data['specifications']))
        
        conn.commit()
        item_id = cursor.lastrowid
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Item added successfully', 'id': item_id})
    except mysql.connector.IntegrityError:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': 'Serial number already exists'})
    except Exception as e:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/inventory/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE inventory 
            SET item_name = %s, item_type = %s, serial_number = %s, 
                location = %s, status = %s, specifications = %s
            WHERE id = %s
        """, (data['item_name'], data['item_type'], data['serial_number'],
              data['location'], data['status'], data['specifications'], item_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Item updated successfully'})
    except mysql.connector.IntegrityError:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': 'Serial number already exists'})
    except Exception as e:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/inventory/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM inventory WHERE id = %s", (item_id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Item deleted successfully'})

@app.route('/logout')
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

if __name__ == '__main__':
    app.run(debug=True)