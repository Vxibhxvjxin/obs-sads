from flask import Flask, render_template, request, redirect, url_for, session, send_file
import os
import pandas as pd
from pymongo import MongoClient  # MongoDB connection
from omr_script import process_omr  # Assuming your script is saved in `omr_script.py`

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a more secure key in production

# MongoDB connection details
MONGO_URI = "mongodb+srv://vj4792:srm_omr@cluster0.xj4tc.mongodb.net/faculty?retryWrites=true&w=majority"

client = MongoClient(MONGO_URI)
db = client['faculty']  # Use your MongoDB database
users_collection = db['credentials']  # Assuming your collection is named 'credentials'

# Define the folder for uploaded files and results
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = os.path.join(UPLOAD_FOLDER, 'output')

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# Route for welcome and login page
@app.route('/')
def welcome():
    return render_template('welcomeLogin.html')

# Route for handling login with MongoDB
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    # Query the MongoDB to check if the username and password are correct
    user = users_collection.find_one({'username': username, 'password': password})

    if user:
        session['logged_in'] = True
        return redirect(url_for('upload_form'))
    else:
        # Pass error message to the template
        error = "Invalid credentials, please try again."
        return render_template('welcomeLogin.html', error=error)

# OMR form and processing routes
@app.route('/upload', methods=['GET', 'POST'])
def upload_form():
    if not session.get('logged_in'):
        return redirect(url_for('welcome'))

    if request.method == 'POST':
        teacher_name = request.form['teacher_name']
        subject = request.form['subject']
        answer_key = request.form['answer_key'].split(',')
        num_of_questions = int(request.form['num_of_questions'])

        uploaded_file = request.files['pdf_file']
        if uploaded_file.filename != '':
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
            uploaded_file.save(pdf_path)
            print(f"Uploaded PDF saved to: {pdf_path}")  # Debugging line

            try:
                # Process OMR
                process_omr(
                    pdf_path, 
                    images_folder_path="images_output", 
                    output_folder=OUTPUT_FOLDER, 
                    answer_key=answer_key, 
                    num_of_questions=num_of_questions
                )
                return redirect(url_for('results'))
            except Exception as e:
                print(f"An error occurred during processing: {e}")
                return "<h1>Error processing the OMR sheet. Check the server logs for more information.</h1>"
    
    return render_template('index.html')

# Route to display OMR results in HTML
@app.route('/results')
def results():
    results_file = os.path.join(app.config['OUTPUT_FOLDER'], 'omr_results.xlsx')

    if not os.path.exists(results_file):
        return "<h1>Results not available yet. Please complete the OMR process.</h1>"

    # Read the Excel file into a pandas DataFrame
    results_df = pd.read_excel(results_file)
    
    # Convert DataFrame to HTML table for rendering
    results_html = results_df.to_html()

    return render_template('results.html', results_html=results_html, download_link=url_for('download_file'))

# Route to download the result file
@app.route('/download')
def download_file():
    results_file = os.path.join(app.config['OUTPUT_FOLDER'], 'omr_results.xlsx')
    if os.path.exists(results_file):
        return send_file(results_file, as_attachment=True)
    else:
        return "<h1>File not found.</h1>"

# Route for handling logout
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('welcome'))

if __name__ == "__main__":
    app.run(debug=True)
