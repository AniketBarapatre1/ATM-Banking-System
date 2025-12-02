# 🏧 ATM Banking System (Python + PostgreSQL)

A fully functional ATM simulation built using **Python**, **PostgreSQL**, and secure **PIN hashing (PBKDF2)**.  
Supports account creation, login, deposits, withdrawals, transfers, history, and monthly statements.

---

## 🚀 Features

### ✔ Account Creation
- Auto-generated **Account Number**
- Auto-generated **Card Number**, **Expiry**, **CVV**
- Secure PIN hashing (PBKDF2)
- Minimum ₹500 opening balance

### ✔ Login System
- Login via **Account + PIN**
- OR **Card Number + CVV + PIN**
- 3 failed-attempt lockout system

### ✔ Banking Operations
- Balance enquiry
- Deposit
- Withdraw (maintains minimum ₹500 balance)
- Transfer to another account
- Last 10 transactions
- Monthly statement exported as **CSV**

### ✔ PostgreSQL Integration
Tables used:
- **accounts**
- **transactions**

All operations performed using `psycopg2`.

---

## 🗂 Project Structure
```

ATM/
│── ATM.py  
│── storage_pg.py  
│── utils.py  
```
