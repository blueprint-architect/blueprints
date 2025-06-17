from flask import Flask, render_template, request, jsonify, session, make_response
import openai
import os
from werkzeug.utils import secure_filename
import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_secret_key_for_testing_only")

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/send_message", methods=['POST'])
def send_message():
    user_message = request.get_json().get('message')
    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        return jsonify({'reply': "Error: OPENAI_API_KEY not set."}), 500
    openai.api_key = api_key

    try:
        if not user_message:
            return jsonify({'reply': "Error: No message provided."}), 400

        chat_history = session.get('chat_history', [])
        messages_payload = []
        if not chat_history:
            messages_payload.append({"role": "system", "content": "You are a helpful chatbot. Users may upload files, and you can discuss their contents if they mention them. Keep your responses concise and informative."})

        messages_payload.extend(chat_history)
        messages_payload.append({"role": "user", "content": user_message})

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages_payload
        )
        bot_reply = response.choices[0].message.content.strip()

        chat_history.append({"role": "user", "content": user_message})
        chat_history.append({"role": "assistant", "content": bot_reply})
        session['chat_history'] = chat_history

        return jsonify({'reply': bot_reply})

    except openai.error.AuthenticationError:
        return jsonify({'reply': "Error: OpenAI API Authentication failed. Check your API key."}), 500
    except openai.error.RateLimitError:
        return jsonify({'reply': "Error: OpenAI API rate limit exceeded. Please try again later."}), 429
    except openai.error.OpenAIError as e:
        app.logger.error(f"OpenAI API error: {str(e)}")
        return jsonify({'reply': f"Error: An OpenAI API error occurred: {str(e)}"}), 500
    except Exception as e:
        app.logger.error(f"An unexpected error occurred: {str(e)}")
        return jsonify({'reply': "Error: An unexpected error occurred on the server."}), 500

@app.route("/clear_chat", methods=['POST'])
def clear_chat():
    session.pop('chat_history', None)
    return jsonify({'status': 'Chat history cleared'})

@app.route("/upload_file", methods=['POST'])
def upload_file():
    if 'files[]' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    files = request.files.getlist('files[]')
    uploaded_filenames = []
    errors = []

    if not files or all(not f.filename for f in files):
        return jsonify({'error': 'No selected files to upload'}), 400

    for file in files:
        if file and file.filename:
            try:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                uploaded_filenames.append(filename)
            except Exception as e:
                app.logger.error(f"Error saving file {file.filename}: {str(e)}")
                errors.append(f"Could not save file {file.filename}.")
        elif file and not file.filename:
             errors.append("A file was received without a filename.")

    if not uploaded_filenames and errors:
         return jsonify({'error': 'Failed to upload any files.', 'details': errors}), 500
    if errors:
        return jsonify({'message': 'Some files uploaded successfully, some failed.', 'filenames': uploaded_filenames, 'errors': errors}), 207

    return jsonify({'message': 'Files uploaded successfully', 'filenames': uploaded_filenames})

@app.route("/export_to_obsidian", methods=['POST'])
def export_to_obsidian():
    data = request.get_json()
    message_content = data.get('content')

    if not message_content:
        return jsonify({'error': 'No content provided for export'}), 400

    # Prepare Markdown content
    # Using a simple title based on the first few words, sanitized.
    title_preview = message_content.split()[:5]
    safe_title = "_".join(filter(str.isalnum, title_preview)).lower()
    if not safe_title: # Handle cases where content might not have alphanumeric characters
        safe_title = "export"

    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"chatbot_{safe_title}_{timestamp}.md"

    markdown_content = f"# ChatBot Response ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M')})\n\n"
    markdown_content += f"{message_content}\n\n"
    markdown_content += "#chatbot #exported"

    response = make_response(markdown_content)
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.headers['Content-Type'] = 'text/markdown; charset=utf-8'

    return response

if __name__ == "__main__":
    app.run(debug=True)
