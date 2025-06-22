
# LinkedIn HR Bot Automation 🤖

This is an intelligent automation bot built using Python and Selenium that helps automate sending personalized connection requests on LinkedIn, especially targeting hiring professionals in the AI/ML/GenAI space. It also integrates with Google Sheets to log and track all sent invitations.

---

## 📌 Features

- 🔐 Logs in to LinkedIn using your credentials
- 🔍 Searches for target profiles (e.g., "GenAI Engineer", "Hiring Manager")
- 📨 Sends personalized connection requests with custom messages
- 📈 Logs each connection (Name + URL + Status) into Google Sheets
- 🔁 Tracks and withdraws old pending invitations (optional)
- 🤖 Mimics human-like behavior to reduce detection:
  - Randomized delays
  - Scrolling and browsing activities
- 📊 Tracks progress and daily connection limits

---

## 🛠️ Tech Stack

- **Python 3**
- **Selenium WebDriver**
- **ChromeDriverManager**
- **gspread** + **Google Sheets API**
- **OAuth2 Client for authentication**

---

## 🚀 How It Works

1. Set your LinkedIn login credentials and target keywords in the script.
2. Connect your Google Sheets using a `credentials.json` file.
3. Launch the bot – it will:
   - Log in to LinkedIn
   - Search for profiles based on multiple keywords
   - Send up to 100 connection requests per day
   - Log each interaction in a Google Sheet

---

## 📂 Project Structure

```
linkedin_hr_bot.py          # Main bot script
credentials.json            # Google Sheets API credentials
linkedin_progress.txt       # Saves progress to avoid duplicate requests
debug_screenshots/          # Stores screenshots when DEBUG_MODE is on
```

---

## ⚠️ Disclaimer

This project is for **educational purposes only**. Automating LinkedIn is against their Terms of Service. Please use responsibly and **do not abuse**. Always respect platform guidelines.

---

## 🧠 Learning Outcomes

- Mastery in Selenium for browser automation
- Real-world experience with anti-bot evasion strategies
- Integration of cloud APIs (Google Sheets)
- Handling dynamic elements and multi-layer DOMs
- Ethical awareness in automation and scraping

---

## 📎 Author

**Santosh R**  
Email: `santosh88386r@gmail.com`  
GitHub: [Your GitHub Link]

---

## 📸 Screenshots (Optional)

You can enable screenshots in `DEBUG_MODE` for testing and documentation purposes.

---

## ✅ Future Improvements

- Add support for 2FA login
- Add a GUI interface using Tkinter/Gradio
- Use a CAPTCHA-solving API (ethically) for checkpoints
