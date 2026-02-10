![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![Flask](https://img.shields.io/badge/Framework-Flask-black)
![License](https://img.shields.io/github/license/Trirez/Captcha)
![Repo Size](https://img.shields.io/github/repo-size/Trirez/Captcha)
![Stars](https://img.shields.io/github/stars/Trirez/Captcha?style=social)
![Forks](https://img.shields.io/github/forks/Trirez/Captcha?style=social)
![Last Commit](https://img.shields.io/github/last-commit/Trirez/Captcha)

A simple CAPTCHA generation and validation web application written in Python.

This project provides a basic system to generate CAPTCHA tests, serve them via a web interface, and verify user responses. A CAPTCHA (Completely Automated Public Turing test to tell Computers and Humans Apart) helps protect forms and services from automated bot access by requiring users to correctly recognize distorted characters or patterns that are easy for humans but hard for machines to solve.

🧠 Features

🔐 CAPTCHA generation: Creates randomized CAPTCHA challenges using Python generators.

📜 Web interface: Serves CAPTCHA images and verification forms via a lightweight web app.

🧪 Testing suite: Includes tests to ensure CAPTCHA generation and validation work as expected.

🗂️ Modular structure: Separate folders for templates, static assets, and generator logic.

📁 Project Structure
Captcha/
├── captcha_generators/     # Code to generate captcha images
├── image_cache/            # Stored/generated captcha assets
├── instance/               # App instance configs (optional)
├── static/                 # Static files (CSS/JS/images)
├── templates/              # HTML templates for web interface
├── app.py                  # Main application routes and logic
├── database.py             # (Optional) storage/verification logic
├── main.py                 # App entry point
├── test_captchas.py        # Unit tests
├── requirements.txt        # Dependencies list

🚀 Getting Started
Prerequisites

Make sure you have Python 3.x installed.

Install Dependencies
```bash
pip install -r requirements.txt
```

Run the App
```bash
python main.py
```

Once running, open a browser and navigate to the provided local address (e.g., http://127.0.0.1:5000
) to view the CAPTCHA form.

📦 How It Works

The app uses Python scripts in captcha_generators/ to create randomized CAPTCHA images.

When a user visits the web page, a new CAPTCHA is displayed.

The user enters the CAPTCHA text, and the app verifies the input.

If the input matches the generated CAPTCHA, the user passes the test.

This is a basic example of a challenge-response test — a widely used security measure that helps distinguish humans from bots.

🧪 Running Tests

To ensure everything works as expected:
```bash
python test_captchas.py
```

📄 License

MIT License (check LICENSE for details)

📌 Notes

This project is intended as a learning example or starting point for adding CAPTCHA protection to Python web applications.

You can customize the CAPTCHA generation (fonts, colors, distortions) to improve security.
