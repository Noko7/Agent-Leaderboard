from flask import Flask, render_template, request, make_response
import sqlite3
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import io
import hashlib
import os
import calendar
import time
from markupsafe import escape
app = Flask(__name__)
DB_PATH = 'database.db'
CACHE_DIR = 'cache/'  # Directory to store cached graphs

# Ensure cache directory exists
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

# Initialize the database
def initialize_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Ensure agents table exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL
        )
    ''')

    # Ensure transactions table exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY,
            agent_id INTEGER,
            volume REAL,
            date TEXT,
            FOREIGN KEY (agent_id) REFERENCES agents(id)
        )
    ''')

    # Add 'address' column if it doesn't exist
    cursor.execute('PRAGMA table_info(transactions)')
    columns = [column[1] for column in cursor.fetchall()]
    if 'address' not in columns:
        cursor.execute('ALTER TABLE transactions ADD COLUMN address TEXT')

    # Populate agents for demo purposes
    cursor.executemany(
        'INSERT OR IGNORE INTO agents (name) VALUES (?)',
        [('Alice',), ('Bob',), ('Charlie',)]
    )

    conn.commit()
    conn.close()


# Generate cache key
def generate_cache_key(graph_type, month):
    key = f"{graph_type}_{month}"
    return hashlib.md5(key.encode()).hexdigest()

# Generate and cache graphs
def generate_graph(graph_type, month):
    cache_key = generate_cache_key(graph_type, month)
    cache_path = os.path.join(CACHE_DIR, f"{cache_key}.png")

    # Check if cached file exists and is newer than 5 seconds
    if os.path.exists(cache_path):
        mtime = os.path.getmtime(cache_path)
        now = time.time()
        if (now - mtime) < 5:
            with open(cache_path, 'rb') as f:
                return io.BytesIO(f.read())

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if graph_type == "monthly_volume":
        month_name = calendar.month_name[int(month.split('-')[1])]
        title = f"Monthly Volume - {month_name}"
        query = '''
            SELECT a.name, SUM(t.volume) AS total_volume
            FROM agents a
            LEFT JOIN transactions t 
                ON a.id = t.agent_id AND strftime('%Y-%m', t.date) = ?
            GROUP BY a.id
            ORDER BY total_volume DESC
        '''
        cursor.execute(query, (month,))
        xlabel = "Volume ($)"
        values_step = 200000
    elif graph_type == "monthly_transactions":
        month_name = calendar.month_name[int(month.split('-')[1])]
        title = f"Monthly Transactions - {month_name}"
        query = '''
            SELECT a.name, COUNT(t.id) AS transaction_count
            FROM agents a
            LEFT JOIN transactions t 
                ON a.id = t.agent_id AND strftime('%Y-%m', t.date) = ?
            GROUP BY a.id
            ORDER BY transaction_count DESC
        '''
        cursor.execute(query, (month,))
        xlabel = "Transactions"
        values_step = 1
    elif graph_type == "ytd_volume":
        ytd_year = datetime.now().strftime('%Y')
        title = f"YTD Volume ({ytd_year})"
        query = '''
            SELECT a.name, SUM(t.volume) AS total_volume
            FROM agents a
            LEFT JOIN transactions t 
                ON a.id = t.agent_id AND strftime('%Y', t.date) = ?
            GROUP BY a.id
            ORDER BY total_volume DESC
        '''
        cursor.execute(query, (ytd_year,))
        xlabel = "Volume (Millions $)"
        values_step = 1000000
    elif graph_type == "ytd_transactions":
        ytd_year = datetime.now().strftime('%Y')
        title = f"YTD Transactions ({ytd_year})"
        query = '''
            SELECT a.name, COUNT(t.id) AS transaction_count
            FROM agents a
            LEFT JOIN transactions t 
                ON a.id = t.agent_id AND strftime('%Y', t.date) = ?
            GROUP BY a.id
            ORDER BY transaction_count DESC
        '''
        cursor.execute(query, (ytd_year,))
        xlabel = "Transactions"
        values_step = 5
    else:
        conn.close()
        return None

    data = cursor.fetchall()
    conn.close()

    agents = [row[0] for row in data] or ["No Data"]
    values = [row[1] if row[1] is not None else 0 for row in data] or [0]

    colors = ['green' if i == 0 else 'gold' if i == 1 else 'silver' if i == 2 else 'skyblue' for i in range(len(values))]

    plt.figure(figsize=(10, 6))
    bars = plt.barh(agents, values, color=colors)

    plt.xlabel(xlabel)
    plt.ylabel("Agents")
    plt.title(title)

    max_value = max(values) if values else values_step
    plt.xticks(range(0, int(max_value) + values_step, values_step),
               [f'{x // 1000000}M' if graph_type == "ytd_volume" else f'{x:,}' for x in range(0, int(max_value) + values_step, values_step)])

    for bar in bars:
        if graph_type in ["monthly_volume", "ytd_volume"]:
            plt.text(bar.get_width(), bar.get_y() + bar.get_height() / 2, f'${bar.get_width():,.2f}', va='center')
        elif graph_type in ["monthly_transactions", "ytd_transactions"]:
            plt.text(bar.get_width(), bar.get_y() + bar.get_height() / 2, f'{int(bar.get_width())}', va='center')

    plt.gca().invert_yaxis()
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()

    with open(cache_path, 'wb') as f:
        f.write(buf.getbuffer())

    return buf

# Routes
@app.route('/')
def index():
    current_month = datetime.now().strftime('%Y-%m')
    return render_template('layout.html', current_month=current_month)

@app.route('/graphs')
def serve_graph():
    graph_type = request.args.get('graph', 'monthly_volume')
    month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    graph_image = generate_graph(graph_type, month)
    if graph_image is None:
        return "Invalid graph type", 400

    response = make_response(graph_image.read())
    response.headers['Content-Type'] = 'image/png'
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    graph_image.close()
    return response

from flask import Flask, render_template, request, redirect, url_for

# @app.route('/deactivate_agent', methods=['POST'])
# def deactivate_agent():
    # conn = sqlite3.connect(DB_PATH)
    # cursor = conn.cursor()
    # message = None

    # try:
    #     # Fetch and validate the agent_id
    #     agent_id = escape(request.form['agent_id']).strip()

    #     # Check if the agent exists and is active
    #     cursor.execute('SELECT id, name FROM agents WHERE id = ? AND status = "active"', (agent_id,))
    #     agent = cursor.fetchone()

    #     if agent:
    #         # Update the agent's status to inactive and rename them to "Other"
    #         cursor.execute('UPDATE agents SET status = "inactive", name = "Other" WHERE id = ?', (agent_id,))
    #         conn.commit()
    #         message = f"Agent {agent[1]} has been deactivated and renamed to 'Other'."
    #     else:
    #         message = "Agent not found or already inactive."
    # except sqlite3.Error as e:
    #     message = f"Database error: {escape(str(e))}"
    # except Exception as e:
    #     message = f"An unexpected error occurred: {escape(str(e))}"
    # finally:
    #     conn.close()

    # return redirect(url_for('admin_panel', message=message))

@app.route('/change_agent_name', methods=['POST'])
def change_agent_name():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    message = None

    try:
        # Fetch and validate input data
        agent_id = escape(request.form['agent_id']).strip()
        new_name = escape(request.form['new_name']).strip()

        # Ensure the agent exists
        cursor.execute('SELECT id, name FROM agents WHERE id = ?', (agent_id,))
        agent = cursor.fetchone()

        if agent:
            # Check if the new name is already taken
            cursor.execute('SELECT id FROM agents WHERE name = ?', (new_name,))
            existing_agent = cursor.fetchone()

            if existing_agent:
                message = f"An agent with the name '{new_name}' already exists. Please choose a different name."
            else:
                # Safely update the agent's name
                cursor.execute('UPDATE agents SET name = ? WHERE id = ?', (new_name, agent_id))
                conn.commit()
                message = f"Agent {agent[1]} has been renamed to '{new_name}'."
        else:
            message = "Agent not found."
    except sqlite3.Error as e:
        message = f"Database error: {escape(str(e))}"
    except Exception as e:
        message = f"An unexpected error occurred: {escape(str(e))}"
    finally:
        conn.close()

    return redirect(url_for('admin_panel', message=message))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    message = None

    try:
        # Safely fetch form data
        agent_id = escape(request.form['agent_id']).strip()
        new_name = escape(request.form['new_name']).strip()

        # Ensure the agent exists
        cursor.execute('SELECT id FROM agents WHERE id = ?', (agent_id,))
        agent = cursor.fetchone()

        if agent:
            # Ensure the new name is not already taken
            cursor.execute('SELECT id FROM agents WHERE name = ?', (new_name,))
            existing_agent = cursor.fetchone()

            if existing_agent:
                message = f"An agent with the name '{new_name}' already exists. Please choose a different name."
            else:
                # Safely update the agent's name
                cursor.execute('UPDATE agents SET name = ? WHERE id = ?', (new_name, agent_id))
                conn.commit()
                message = f"Agent name changed successfully to '{new_name}'."
        else:
            message = "Agent not found."
    except sqlite3.Error as e:
        message = f"Database error: {escape(str(e))}"
    except Exception as e:
        message = f"An unexpected error occurred: {escape(str(e))}"
    finally:
        conn.close()

    return redirect(url_for('admin_panel', message=message))


@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    message = None
    agents = []
    transactions = []

    try:
        if request.method == 'POST':
            if 'add_agent' in request.form:
                agent_name = escape(request.form['agent_name'].strip())
                cursor.execute('INSERT INTO agents (name) VALUES (?)', (agent_name,))
                message = f"Agent '{agent_name}' added successfully!"
            elif 'add_transaction' in request.form:
                agent_id = escape(request.form['transaction_agent_id'])
                volume = float(request.form['transaction_volume'])
                date = escape(request.form['transaction_date'])
                address = escape(request.form['transaction_address'].strip())
                cursor.execute(
                    'INSERT INTO transactions (agent_id, volume, date, address) VALUES (?, ?, ?, ?)',
                    (agent_id, volume, date, address)
                )
                message = "Transaction added successfully!"
            elif 'remove_agent' in request.form:
                agent_id = escape(request.form['agent_id'])
                cursor.execute('DELETE FROM agents WHERE id = ?', (agent_id,))
                cursor.execute('DELETE FROM transactions WHERE agent_id = ?', (agent_id,))
                message = "Agent removed successfully!"
            elif 'remove_transaction' in request.form:
                transaction_id = escape(request.form['transaction_id'])
                cursor.execute('DELETE FROM transactions WHERE id = ?', (transaction_id,))
                message = "Transaction removed successfully!"

            # Redirect after successful POST to prevent resubmission
            conn.commit()
            return redirect(url_for('admin_panel', message=message))

        # Handle GET requests and search functionality
        search_query = escape(request.args.get('search_query', '').strip())
        if search_query:
            query = """
                SELECT t.id, a.name, t.volume, t.date, t.address
                FROM transactions t
                JOIN agents a ON t.agent_id = a.id
                WHERE a.name LIKE ? OR t.address LIKE ? OR t.date LIKE ?
                ORDER BY t.date DESC
            """
            search_term = f"%{search_query}%"
            transactions = cursor.execute(query, (search_term, search_term, search_term)).fetchall()
        else:
            transactions = cursor.execute('''
                SELECT t.id, a.name, t.volume, t.date, t.address
                FROM transactions t
                JOIN agents a ON t.agent_id = a.id
            ''').fetchall()

        agents = cursor.execute('SELECT * FROM agents').fetchall()

    except sqlite3.Error as e:
        message = f"Database error: {escape(str(e))}"
    except Exception as e:
        message = f"An unexpected error occurred: {escape(str(e))}"
    finally:
        conn.commit()
        conn.close()

    return render_template('admin.html', agents=agents, transactions=transactions, message=message)
# Initialize the database before starting the app
initialize_database()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)