import gridfs
from gtts import gTTS
from pymongo import MongoClient
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template_string, send_file
import io
from urllib.parse import quote_plus

chat_map = {}

# Set up Gemini API key (replace with your key)
GOOGLE_API_KEY = "" 
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize Gemini model
model = genai.GenerativeModel('gemini-1.5-flash')

# Initialize Flask App
app = Flask(__name__)

# MongoDB connection string with your credentials
uri = "mongodb+srv://Shreyash:Connect@cluster0.3bukhbc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Connect to MongoDB
client = MongoClient(uri)
db = client['Cluster0']  # Replace with your database name
users_collection = db["user"]
fs = gridfs.GridFS(db)

print('Success connection.')

def process_pdf_with_gemini(pdf, context):
    """
    Uploads a PDF to Gemini and receives a processed response.
    """
    pdf_data = pdf.read()
    response = model.generate_content([{"mime_type": "application/pdf", "data": pdf_data}, context])
    return response.text

def authenticate(username, password):
    user = users_collection.find_one({"username": username})
    if user and user["password"] == password:
        return user
    return None

def get_pdf_id(filename, username):
    file_doc = fs.find_one({"filename": filename, "username": username})
    return file_doc._id if file_doc else None  # Return ObjectId if found

@app.route('/')
def home():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome to Flask</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                margin-top: 50px;
            }
            h1 {
                color: #4CAF50;
            }
        </style>
    </head>
    <body>
        <h1>Welcome to the Backend home of AI Web App</h1>
        <p> this is cactus track , use available api services </p>
        <p> copyright @2025 </p>
    </body>
    </html>
    """
    return render_template_string(html_content)

# Route: Register User (For Testing Purposes)
@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username")
    password = request.form.get("password")
    
    if not username or not password:
        return jsonify({"error": "Missing user fields"}), 400

    if users_collection.find_one({"username": username}):
        return jsonify({"error": "User already exists"}), 400

    users_collection.insert_one({
        "username": username,
        "password": password,
        "pdfs": []  # Initialize empty PDF list
    })
    return jsonify({"message": "User registered successfully"}), 200

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    
    if not username or not password:
        return jsonify({"error": "Missing user fields"}), 400

    if authenticate(username, password):
        return jsonify({"message": "User authenticated"}), 200
    
    return jsonify({"error": "Invalid credentials"}), 400

# Route: List all PDFs
@app.route("/user/pdfs", methods=["POST"])
def list_pdfs():
    username = request.form.get("username")
    password = request.form.get("password")
    
    if not username or not password:
        return jsonify({"error": "Missing user fields"}), 400

    user = authenticate(username, password)
    
    if not user:
        return jsonify({"error": "Invalid credentials"}), 400

    a = [fs.get(x).filename for x in user.get("pdfs", [])]
    return jsonify({"pdfs": a}), 200

# Route: Add a PDF
@app.route("/user/add_pdf", methods=["POST"])
def add_pdf():
    username = request.form.get("username")
    password = request.form.get("password")
    print(username,password)
    if not username or not password:
        return jsonify({"error": "Missing user fields"}), 400

    user = authenticate(username, password)
    
    if not user:
        return jsonify({"error": "Invalid credentials"}), 400

    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not file.filename.endswith(".pdf"):
        return jsonify({"error": "Invalid file type, only PDFs allowed"}), 400
    
    a = [fs.get(x).filename for x in user.get("pdfs", [])]
    if file.filename in a:
        return jsonify({"message": "File-name already exists (mistake-upload)"}), 200
    
    # Save PDF file
    file_id = fs.put(file, filename=file.filename, username=username)
    users_collection.update_one(
        {"username": username},
        {"$push": {"pdfs": file_id}}
    )
    return jsonify({"message": "File uploaded successfully", "file_name": file.filename}), 200

# Route: Remove a PDF
@app.route("/user/remove_pdf", methods=["POST"])
def remove_pdf():
    username = request.form.get("username")
    password = request.form.get("password")
    pdf_name = request.form.get("pdf_name")
    print(username,password,pdf_name)

    if not username or not password or not pdf_name:
        return jsonify({"error": "Missing user fields"}), 400

    user = authenticate(username, password)
    if not user: return jsonify({"error": "Invalid credentials"}), 400

    pdf_id = get_pdf_id(pdf_name, username)
    if pdf_id not in user["pdfs"]: 
        return jsonify({"error": "PDF not found"}), 400

    users_collection.update_one(
        {"username": username},
        {"$pull": {"pdfs": pdf_id}}
    )
    fs.delete(pdf_id)
    
    return jsonify({"message": "PDF removed successfully"}), 200

@app.route("/user/query_pdf", methods=["POST"])
def query_pdf():
    username = request.form.get("username")
    password = request.form.get("password")
    query = request.form.get("query")
    
    print(username,password,query)

    if not username or not password or not query:
        return jsonify({"error": "Missing user fields"}), 400

    user = authenticate(username, password)
    if not user: return jsonify({"error": "Invalid credentials"}), 400
    
    try:
        print(chat_map[username])
        print("hello")
        response = chat_map[username].send_message(query)
        print(response)
        return jsonify({"data": response}), 200
    except Exception as e:
        return f"Error: {str(e)}", 500


@app.route("/user/summary_pdf", methods=["POST"])
def summary_pdf():
    username = request.form.get("username")
    password = request.form.get("password")
    pdf_name = request.form.get("pdf_name")
    print(username,password,pdf_name)

    if not username or not password or not pdf_name:
        return jsonify({"error": "Missing user fields"}), 400

    user = authenticate(username, password)
    if not user: return jsonify({"error": "Invalid credentials"}), 400

    pdf_id = get_pdf_id(pdf_name, username)
    
    if pdf_id not in user["pdfs"]: 
        return jsonify({"error": "PDF not found"}), 400
    pdf = fs.get(pdf_id)
    
    custom_context = "Provide detailed summary."
    pdf_text = process_pdf_with_gemini(pdf, custom_context)
    print("PDF processed successfully")
    
    # Initialize chat session with PDF context
    chat_session = model.start_chat(history=[{"role": "user", "parts": [{"text": f"process the following document and list everything. You should use this information to answer questions: {pdf_text}"}]}]) 
    
    chat_map[username] = chat_session
    return jsonify({"message": "PDF processed successfully", "data": pdf_text}), 200

@app.route("/user/podcast_pdf", methods=["POST"])
def podcast_pdf():
    username = request.form.get("username")
    password = request.form.get("password")
    pdf_name = request.form.get("pdf_name")
    print(username, password, pdf_name)

    if not username or not password or not pdf_name:
        return jsonify({"error": "Missing user fields"}), 400

    user = authenticate(username, password)
    if not user: return jsonify({"error": "Invalid credentials"}), 400

    pdf_id = get_pdf_id(pdf_name, username)
    
    print(pdf_id)
    print(pdf_id in user["pdfs"])
    print(user["pdfs"])
    if pdf_id not in user["pdfs"]: 
        return jsonify({"error": "PDF not found"}), 400
    pdf = fs.get(pdf_id)
    
    custom_context = "Provide a 3 min (200 words) podcast script and dont provide headers, just start narating the script like that in an actual podcast for the PDF discussing the key points."
    text = process_pdf_with_gemini(pdf, custom_context)
    print("PDF processed successfully")
    
    tts = gTTS(text=text, lang="en", slow=False)
    audio_buffer = io.BytesIO()
    tts.write_to_fp(audio_buffer)  # Write audio data to buffer
    audio_buffer.seek(0)  # Move pointer to the beginning

    # Send the podcast as an audio file
    return send_file(audio_buffer, as_attachment=True, mimetype="audio/mp3", download_name="podcast.mp3")

if __name__ == "__main__":
    app.run(debug=True)
