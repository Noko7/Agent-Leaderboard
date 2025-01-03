import sqlite3
import random
import datetime

DB_PATH = 'database.db'  # Same directory as this script

# Sample address components for random generation
STREET_NAMES = ["Main", "Elm", "Maple", "Pine", "Oak", "Cedar", "1st", "2nd", "3rd"]
CITY_NAMES = ["Springfield", "Rivertown", "Hill Valley", "Lakeside", "Fairview"]
STATES = ["CA", "TX", "NY", "FL", "IL"]

def get_agent_ids():
    """
    Fetch all agent IDs from the existing 'agents' table.
    Returns a list of integer IDs.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM agents")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def random_date_2025():
    """
    Return a random date (as a string) in the year 2025.
    """
    start_date = datetime.date(2025, 1, 1)
    end_date = datetime.date(2025, 12, 31)
    delta = end_date - start_date
    rand_days = random.randint(0, delta.days)
    date_obj = start_date + datetime.timedelta(days=rand_days)
    return date_obj.isoformat()  # e.g. '2025-05-17'

def random_address():
    """
    Generate a random address as a string.
    Format: '123 Main St, Springfield, CA'
    """
    street_number = random.randint(100, 9999)
    street_name = random.choice(STREET_NAMES)
    city = random.choice(CITY_NAMES)
    state = random.choice(STATES)
    return f"{street_number} {street_name} St, {city}, {state}"

def generate_transactions(num=300):
    """
    Generate 'num' transaction rows as tuples matching:
      (agent_id, volume, date, address)
    Each row has:
    - Around $100k volume
    - A random date in 2025
    - A random address
    """
    agent_ids = get_agent_ids()
    if not agent_ids:
        print("No agents found in the database. Add agents before generating transactions.")
        return []

    transactions = []
    for _ in range(num):
        agent_id = random.choice(agent_ids)
        volume = abs(round(random.gauss(100000, 20000), 2))  # Mean 100k, std dev 20k
        date_str = random_date_2025()
        address = random_address()

        transactions.append((agent_id, volume, date_str, address))
    return transactions

def insert_transactions(transactions):
    """
    Insert the given list of (agent_id, volume, date, address) tuples
    into the existing 'transactions' table in database.db.
    """
    if not transactions:
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # The table already exists with columns: id, agent_id, volume, date, address
    insert_sql = """
        INSERT INTO transactions (agent_id, volume, date, address)
        VALUES (?, ?, ?, ?)
    """
    cursor.executemany(insert_sql, transactions)
    conn.commit()
    print(f"{cursor.rowcount} transaction(s) inserted into the 'transactions' table.")
    conn.close()

def main():
    transactions = generate_transactions(300)  # Generate 300 random rows
    insert_transactions(transactions)

if __name__ == "__main__":
    main()
