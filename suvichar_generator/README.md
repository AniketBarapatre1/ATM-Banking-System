# 🌅 Daily Suvichar Generator  
A simple Python tool that fetches a daily inspirational quote, emails it to you, and stores it in a CSV history log.

---

## ⭐ Features  
- Fetches a random quote from **ZenQuotes API**  
- Sends the quote to your Gmail using **SMTP + App Password**  
- Stores every quote in `suvichar_history.csv`  
- Loads email credentials securely from `.env`  
- Can be automated daily via Task Scheduler (Windows)  
- Lightweight, dependency-free except for `requests` + `python-dotenv`

---

## 📁 Project Structure  
```
suvichar_generator/
│
├── daily_suvichar.py       # Main script
├── suvichar_history.csv    # Auto-generated quote log
├── .env                    # Stored locally (ignored in Git)
└── .gitignore              # Ignore rules
```

