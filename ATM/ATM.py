

from utils import hash_pin, check_pin, sanitize_card
import random
import csv
from datetime import datetime, timedelta
import storage_pg as db

# Simple ATM project I built for practice
# Added card login + OTP just to make it more realistic

def create():
    print("\n--- CREATE ACCOUNT ---")
    name = input("Name: ").strip()
    if len(name) < 2: print("Invalid name"); return

    pin = input("Set 4-digit PIN: ").strip()
    if not (pin.isdigit() and len(pin) == 4): print("PIN must be 4 digits"); return
    if pin != input("Confirm PIN: ").strip(): print("PIN didn't match"); return

    try:
        bal = float(input("Initial deposit (min ₹500): ₹"))
        if bal < 500: print("Min ₹500 needed"); return
    except ValueError:
        print("Invalid amount"); return

    acc = str(random.randint(10 ** 9, 10 ** 10 - 1))
    card = f"{random.randint(1000, 9999)} {random.randint(1000, 9999)} {random.randint(1000, 9999)} {random.randint(1000, 9999)}"
    exp = (datetime.now() + timedelta(days=1825)).strftime("%m/%y")
    cvv = str(random.randint(100, 999))

    db.create_account(acc, name, hash_pin(pin), bal, card=card, expiry=exp, cvv=cvv)
    print("\nAccount created!")
    print("Account:", acc)
    print("Card:", card, "Exp:", exp, "CVV:", cvv)
    print("Balance: ₹", bal)


class ATM:

    def __init__(self):
        # TODO: later try GUI version (maybe Tkinter)
        self.user = None

    def login(self):
        print("\n--- LOGIN ---\n1.Account+PIN\n2.Card+CVV+PIN")
        ch = input("Choice: ").strip()

        if ch == "1":
            acc = input("Account: ").strip()
            acct = db.get_account(acc)
            if not acct:
                print("Not found")
                return False

        elif ch == "2":
            raw_card = input("Card: ").strip()
            card = sanitize_card(raw_card)
            cvv = input("CVV: ").strip()
            acct = db.find_account_by_card(card, cvv)
            if not acct:
                print("Invalid card/cvv")
                return False
            acc = acct['account_id']

        else:
            print("Invalid choice")
            return False

        for i in range(3):
            if check_pin(input("PIN: ").strip(), acct['pin_hash']):
                self.user = acc
                print("Login ok")
                return True
            print("Wrong PIN. Left:", 2 - i)

        print("Locked")
        return False

    def print_slip(self, type, amount, desc=""):
        acct = db.get_account(self.user)
        date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        balance = acct["balance"]

        card_info = ""
        if acct.get("card"):
            card_info = "Card: XXXX XXXX XXXX " + acct["card"].split()[-1]

        details = ""
        if desc:
            details = "Details: " + desc
        print(
            f"\n{'=' * 40}\n"
            f" TRANSACTION RECEIPT\n"
            f"{'=' * 40}\n"
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Account: {self.user}\n"
            f"{card_info}\n\n"
            f"Transaction: {type}\n"
            f"{details}"
            f"Amount: ₹{amount:.2f}\n"
            f"Balance: ₹{acct['balance']:.2f}\n"
            f"{'=' * 40}\n"
            f"   Thank you for banking with us!\n"
            f"{'=' * 40}"
        )

    def balance(self):
        # Show current balance & card information
        acct = db.get_account(self.user)
        print(f"\n Balance: ₹{acct['balance']:.2f}")
        if acct.get('card'):
            print(f" Card: {acct['card']} | Expiry: {acct['expiry']}")

    def deposit(self):
        try:
            amt = float(input("Deposit amount: ₹"))
            if amt <= 0: print("Invalid amount"); return
            new_bal = db.deposit(self.user, amt)
            print("Deposited ₹", amt, "| Balance ₹", new_bal)
            if input("Print slip? (y/n): ").lower() == 'y':
                self.print_slip("DEPOSIT", amt)
        except ValueError:
            print("Invalid input")

    def withdraw(self):
        try:
            amt = float(input("\nWithdraw: ₹"))
            new_bal = db.withdraw(self.user, amt)
            print(f"Withdrawn ₹{amt:.2f} | Balance: ₹{new_bal:.2f}")
            if input("Print slip? (y/n): ").lower() == 'y':
                self.print_slip("WITHDRAWAL", amt)
        except Exception as e:
            print("", e)

    def transfer(self):
        to = input("Send to (acc no): ").strip()
        if to == self.user:
            return print("Invalid account")
        if not db.get_account(to):
            return print("Invalid account")
        try:
            amt = float(input("Amount ₹: "))
            db.transfer(self.user, to, amt)
            acct = db.get_account(self.user)
            print(f"Sent ₹{amt:.2f}. New balance: ₹{acct['balance']:.2f}")
            if input("Slip? (y/n): ").lower() == "y":
                self.print_slip("TRANSFER", amt, f"To ***{to[-4:]}")
        except Exception as e:
            print("Enter valid number or error:", e)


    def change_pin(self):
        print("\nChange PIN")
        old = input("Current PIN: ").strip()
        acct = db.get_account(self.user)
        if not check_pin(old, acct['pin_hash']):
            return print("Wrong PIN")
        new = input("New PIN (4 digits): ").strip()
        if len(new) != 4 or not new.isdigit() or new != input("Confirm PIN: ").strip():
            return print("PIN mismatch")
        # update via SQL
        with db.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE accounts SET pin_hash = %s WHERE account_id = %s", (hash_pin(new), self.user))
            conn.commit()
        print("PIN updated")
        return None

    def statement(self):
        print("\nMonthly Statement")
        try:
            m = int(input("Month (1-12): "))
            y = int(input("Year: "))
            if not 1 <= m <= 12:
                return print("Invalid month")
        except:
            return print("Invalid input")

        rows = db.get_transactions(self.user, month=m, year=y)
        if not rows:
            return print("No transactions found")

        file = f"statement_{self.user}_{m}_{y}.csv"
        with open(file, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Date", "Description", "Type", "Amount", "Balance"])
            for t in rows:
                w.writerow([t['created_at'], t['description'], t['type'], t['amount'], f"{t['balance_after']:.2f}"])
        print("Statement saved:", file)
        return None

    def history(self):
        # Show last 10 transactions
        print("\n" + "=" * 50 + "\n    HISTORY\n" + "=" * 50)
        trans = db.get_transactions(self.user)
        if not trans:
            print("No transactions")
        else:
            for t in trans[-10:]:
                print(
                    f"\n{t['created_at']}\n{t['description']} {'+' if t['type'] == 'credit' else '-'}₹{t['amount']:.2f}  (Bal: ₹{t['balance_after']:.2f})")

    def menu(self):
        while True:
            print(
                f"\n{'=' * 50}\n{db.get_account(self.user)['name']}'s Account"
                f"\n{'=' * 50}\n1.Balance 2.Deposit 3.Withdraw 4.Transfer 5.History"
                f"\n6.Statement 7.Change PIN 8.Logout")

            choice = input("\nChoice: ").strip()
            if choice == "1":
                self.balance()
            elif choice == "2":
                self.deposit()
            elif choice == "3":
                self.withdraw()
            elif choice == "4":
                self.transfer()
            elif choice == "5":
                self.history()
            elif choice == "6":
                self.statement()
            elif choice == "7":
                self.change_pin()
            elif choice == "8":
                print(" Thank you for using ATM. Goodbye!")
                self.user = None
                break

    def run(self):
        # Main home screen
        while True:
            print(f"\n{'=' * 50}\nATM SYSTEM\n{'=' * 50}\n1.Create \n2.Login \n3.Exit")
            choice1 = input("\nChoice: ").strip()
            if choice1 == "1":
                create()
            elif choice1 == "2":
                if self.login():
                    self.menu()
            elif choice1 == "3":
                print("\nThank you!\n")
                break
            else:
                print("Invalid option")

if __name__ == "__main__":
    try:
        ATM().run()
    except KeyboardInterrupt:
        print("\nProgram stopped manually. Exiting safely..")


