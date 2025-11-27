# Companion - AI Mental Health Chatbot

A privacy-focused, AI-powered companion designed to provide comfort, support, and a listening ear. Built with Python, Flask, and Google Gemini.

![UI Screenshot](https://via.placeholder.com/800x400?text=Companion+UI+Preview) 
*(Replace with actual screenshot if available)*

## 🌟 Features

- **Empathetic AI**: Powered by Google Gemini, "Companion" offers warm, validating, and human-like support without pretending to be human.
- **Privacy First**: All conversation history is stored **locally** and **encrypted** using Fernet (AES). No data is sent to any cloud database (except the current message to Gemini for processing).
- **Mood Tracking**: Uses `vaderSentiment` to analyze your mood in real-time and adapt its responses.
- **Premium Design**: A calming "Glassmorphism" UI designed to be gentle on the eyes and mind.
- **Crisis Safety**: Automatically detects crisis keywords and provides safety resources.
- **Offline Capable**: If the AI service is unavailable (or no API key is set), the bot seamlessly switches to a built-in comforting response engine.

## 🛠️ Tech Stack

- **Backend**: Python, Flask
- **AI**: Google Gemini Pro (`google-generativeai`)
- **Sentiment Analysis**: `vaderSentiment`
- **Security**: `cryptography` (Fernet encryption)
- **Frontend**: HTML5, CSS3 (Glassmorphism), JavaScript

## 🚀 Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/mental-health-chatbot.git
    cd mental-health-chatbot
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure API Key**:
    - Open `app.py`.
    - Replace the placeholder `GOOGLE_API_KEY` with your own key from [Google AI Studio](https://aistudio.google.com/).
    - *Recommended*: Use an environment variable for security.

4.  **Run the application**:
    ```bash
    python3 app.py
    ```

5.  **Open in Browser**:
    Visit `http://localhost:5001` to start chatting.

## 🔒 Privacy & Security

- **Local Storage**: Your chat history lives in `chat_data.enc` on your own machine.
- **Encryption**: The file is encrypted with a locally generated `secret.key`. Without this key, the data is unreadable.
- **No Cloud Persistence**: We do not store your data on any external servers.

## 🤝 Contributing

Feel free to fork this project and submit pull requests. Suggestions for making the bot more comforting or adding new features are welcome!

## 📄 License

This project is open-source and available under the MIT License.
