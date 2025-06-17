# Obsidian ChatBot

## Description

Obsidian ChatBot is a web-based chatbot application built with Flask and powered by the OpenAI API. It allows users to have interactive conversations, maintains chat history, supports file uploads via drag-and-drop, and enables exporting individual bot responses to Obsidian-compatible Markdown files.

## Features

*   **Interactive Chat:** Real-time conversation with an AI model (OpenAI's GPT series).
*   **Chat History:** Remembers previous messages in the current session for contextual responses.
*   **File Uploads:** Users can drag and drop files into the chat interface. While the content isn't directly injected into the AI context automatically yet, this feature allows users to upload files that can then be discussed by referencing their names.
*   **Export to Obsidian:** Individual bot responses can be exported as Markdown files, suitable for direct use in Obsidian vaults, complete with a title and relevant tags.
*   **Clear Chat:** Option to clear the current chat history and start a new conversation.
*   **User-Friendly Interface:** Styled for ease of use and readability.

## Prerequisites

*   Python 3.7+
*   pip (Python package installer)
*   An OpenAI API Key

## Setup and Installation

1.  **Clone the Repository (or Download Files):**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```
    (If you downloaded the files as a ZIP, extract them to a directory of your choice.)

2.  **Create a Virtual Environment (Recommended):**
    *   On Linux/macOS:
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```
    *   On Windows:
        ```bash
        python -m venv venv
        venv\Scripts\activate
        ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configuration (Environment Variables):**
    The application requires the following environment variables to be set:

    *   `OPENAI_API_KEY`: Your API key from OpenAI.
    *   `FLASK_SECRET_KEY`: A secret key for Flask session management. This should be a long, random string. You can generate one using Python:
        ```python
        import secrets
        print(secrets.token_hex(32))
        ```

    **How to set environment variables:**

    *   **Linux/macOS (Bash/Zsh):**
        ```bash
        export OPENAI_API_KEY='your_openai_api_key_here'
        export FLASK_SECRET_KEY='your_generated_flask_secret_key'
        ```
        You can add these lines to your shell's profile file (e.g., `~/.bashrc`, `~/.zshrc`) for them to persist across sessions. Remember to `source` the file after editing.

    *   **Windows (Command Prompt):**
        ```cmd
        set OPENAI_API_KEY=your_openai_api_key_here
        set FLASK_SECRET_KEY=your_generated_flask_secret_key
        ```
    *   **Windows (PowerShell):**
        ```powershell
        $env:OPENAI_API_KEY="your_openai_api_key_here"
        $env:FLASK_SECRET_KEY="your_generated_flask_secret_key"
        ```
        For persistent environment variables on Windows, search for "environment variables" in the system settings.

    *   **Using a `.env` file (Alternative):**
        While this application does not load `.env` files by default, you can modify `app.py` to use a library like `python-dotenv` if you prefer. Install it (`pip install python-dotenv`) and add the following to the beginning of `app.py`:
        ```python
        from dotenv import load_dotenv
        load_dotenv()
        ```
        Then, create a `.env` file in the project root:
        ```
        OPENAI_API_KEY=your_openai_api_key_here
        FLASK_SECRET_KEY=your_generated_flask_secret_key
        ```
        **Remember to add `.env` to your `.gitignore` file to avoid committing your secrets.**

## Running the Application

Once the setup is complete and environment variables are configured:

1.  Ensure your virtual environment is activated.
2.  Run the Flask development server:
    ```bash
    flask run
    ```
    Alternatively, you can run:
    ```bash
    python app.py
    ```
    (The `app.py` file includes `app.run(debug=True)` which is suitable for development.)

3.  Open your web browser and navigate to:
    `http://127.0.0.1:5000` (or the URL provided in your terminal).

## How to Use

*   **Chatting:** Type your message in the input field at the bottom and press Enter or click "Send".
*   **File Uploads:** Drag files from your computer and drop them onto the designated "Drop files here" area. A system message will confirm successful uploads. You can then refer to these files in your conversation.
*   **Exporting Messages:** Each message from the bot will have an "Export to Obsidian" button. Click this button to download a Markdown file of that specific response, formatted for Obsidian.
*   **Clearing Chat:** Click the "Clear Chat" button at the top right of the chat interface to reset the conversation history for the current session.

## File Structure

```
.
├── app.py                # Main Flask application logic, routes, and API integration.
├── requirements.txt      # Python package dependencies.
├── static/               # Contains static assets (CSS, JavaScript if separated).
│   └── style.css         # Stylesheet for the application.
├── templates/            # HTML templates for the Flask application.
│   └── index.html        # Main HTML page for the chat interface.
├── uploads/              # Default directory where uploaded files are stored.
│                         # (This directory is created automatically if it doesn't exist)
└── README.md             # This file.
```

---
*Note: The `uploads/` directory is created automatically when the application starts if it doesn't already exist. Ensure the application has write permissions for this directory.*
