import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager


DB_CONFIG = {
    'dbname': 'atm_db',
    'user': 'postgres',
    'password': 'Password',
    'host': 'localhost',
    'port': 5432
}

@contextmanager
def get_conn():
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        yield conn
    finally:
        conn.close()

def create_account(account_id, name, pin_hash, balance, card=None, expiry=None, cvv=None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO accounts(account_id, name, pin_hash, balance, card, expiry, cvv)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (account_id, name, pin_hash, balance, card, expiry, cvv))

            # Initial history row
            cur.execute("""
                INSERT INTO transactions(account_id, type, amount, description, balance_after)
                VALUES (%s, 'credit', %s, 'Account Created', %s)
            """, (account_id, balance, balance))

        conn.commit()

def get_account(account_id):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM accounts WHERE account_id = %s", (account_id,))
            return cur.fetchone()

def find_account_by_card(card_digits, cvv):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM accounts 
                WHERE regexp_replace(card, '\\D', '', 'g') = %s 
                AND cvv = %s
            """, (card_digits, cvv))
            return cur.fetchone()


def deposit(account_id, amount):
    with get_conn() as conn:
        with conn.cursor() as cur:

            cur.execute("SELECT balance FROM accounts WHERE account_id = %s FOR UPDATE", (account_id,))
            row = cur.fetchone()
            if not row:
                raise ValueError("Account not found")

            new_bal = float(row[0]) + float(amount)

            # Update balance
            cur.execute("""
                UPDATE accounts SET balance = %s WHERE account_id = %s
            """, (new_bal, account_id))

            # Insert transaction
            cur.execute("""
                INSERT INTO transactions(account_id, type, amount, description, balance_after)
                VALUES (%s, 'credit', %s, 'Deposit', %s)
            """, (account_id, amount, new_bal))

        conn.commit()
    return new_bal

def withdraw(account_id, amount, min_balance=500.0):
    with get_conn() as conn:
        with conn.cursor() as cur:

            cur.execute("SELECT balance FROM accounts WHERE account_id = %s FOR UPDATE", (account_id,))
            row = cur.fetchone()
            if not row:
                raise ValueError("Account not found")

            bal = float(row[0])

            if amount <= 0 or bal - amount < min_balance:
                raise ValueError("Insufficient funds or invalid amount")

            new_bal = bal - amount

            cur.execute("""
                UPDATE accounts SET balance = %s WHERE account_id = %s
            """, (new_bal, account_id))

            cur.execute("""
                INSERT INTO transactions(account_id, type, amount, description, balance_after)
                VALUES (%s,'debit',%s,'Withdrawal',%s)
            """, (account_id, amount, new_bal))

        conn.commit()
    return new_bal

def transfer(from_acc, to_acc, amount, min_balance=500.0):
    with get_conn() as conn:
        try:
            with conn.cursor() as cur:
                conn.autocommit = False

                # Lock both accounts to avoid race
                a, b = (from_acc, to_acc) if from_acc < to_acc else (to_acc, from_acc)
                cur.execute("SELECT account_id FROM accounts WHERE account_id IN (%s,%s) FOR UPDATE", (a, b))

                # Check balance of sender
                cur.execute("SELECT balance FROM accounts WHERE account_id = %s", (from_acc,))
                row = cur.fetchone()
                if not row:
                    raise ValueError("From account not found")

                bal = float(row[0])
                if amount <= 0 or bal - amount < min_balance:
                    raise ValueError("Insufficient funds")

                # Debit sender
                cur.execute("UPDATE accounts SET balance = balance - %s WHERE account_id = %s",
                            (amount, from_acc))

                # Credit receiver
                cur.execute("UPDATE accounts SET balance = balance + %s WHERE account_id = %s",
                            (amount, to_acc))

                # Fetch new balances
                cur.execute("SELECT balance FROM accounts WHERE account_id = %s", (from_acc,))
                new_from = float(cur.fetchone()[0])

                cur.execute("SELECT balance FROM accounts WHERE account_id = %s", (to_acc,))
                new_to = float(cur.fetchone()[0])

                # Insert transactions
                cur.execute("""
                    INSERT INTO transactions(account_id, type, amount, description, balance_after)
                    VALUES (%s,'debit',%s,%s,%s)
                """, (from_acc, amount, f"Transfer to {to_acc[-4:]}", new_from))

                cur.execute("""
                    INSERT INTO transactions(account_id, type, amount, description, balance_after)
                    VALUES (%s,'credit',%s,%s,%s)
                """, (to_acc, amount, f"Transfer from {from_acc[-4:]}", new_to))

            conn.commit()

        except Exception:
            conn.rollback()
            raise

def get_transactions(account_id, month=None, year=None):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:

            if month and year:
                cur.execute("""
                    SELECT created_at, description, type, amount, balance_after
                    FROM transactions
                    WHERE account_id = %s 
                    AND extract(month from created_at) = %s 
                    AND extract(year from created_at) = %s
                    ORDER BY created_at
                """, (account_id, month, year))

            else:
                cur.execute("""
                    SELECT created_at, description, type, amount, balance_after 
                    FROM transactions
                    WHERE account_id = %s
                    ORDER BY created_at
                """, (account_id,))

            return cur.fetchall()
