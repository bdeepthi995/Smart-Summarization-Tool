from flask import Flask, render_template, request, send_file, send_from_directory
from werkzeug.utils import secure_filename
from transformers import BartForConditionalGeneration, BartTokenizer
from googletrans import Translator
import os
import docx
import pandas as pd
from PyPDF2 import PdfReader
import requests
from bs4 import BeautifulSoup
from complaint_classifier import ComplaintClassifier

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize models
model = BartForConditionalGeneration.from_pretrained("facebook/bart-large-cnn")
tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-cnn")
translator = Translator()
complaint_classifier = ComplaintClassifier()

def abstractive_summary(text, length="medium"):
    """Generate abstractive summary using BART model"""
    if not text or not isinstance(text, str):
        return "No valid text content to summarize"
    
    length_map = {"short": 50, "medium": 150, "long": 300, "very long": 500}
    max_length = length_map.get(length, 150)

    inputs = tokenizer([text], max_length=1024, return_tensors="pt", truncation=True)
    summary_ids = model.generate(inputs['input_ids'], max_length=max_length, min_length=50, num_beams=4, length_penalty=2.0)
    return tokenizer.decode(summary_ids[0], skip_special_tokens=True)

@app.route('/')
def index():
    return render_template('index.html')

def scrape_website(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        text = " ".join([p.get_text() for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])])
        return text
    except Exception as e:
        return f"Error scraping website: {str(e)}"
    
    

# [Previous imports and setup remain the same until the process route]

@app.route('/process', methods=['POST'])
def process():
    input_type = request.form.get('file_type')
    is_excel = False
    file_contents = []

    try:
        if input_type == 'text':
            content = request.form.get('text_area', '')
            if content.strip():
                file_contents.append({
                    'type': 'text',
                    'content': content
                })
        elif input_type == 'document':
            files = request.files.getlist('file_input')
            for file in files:
                if file.filename == '':
                    continue
                    
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
                file.save(file_path)
                
                try:
                    if file.filename.lower().endswith('.txt'):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            file_content = f.read()
                    elif file.filename.lower().endswith('.docx'):
                        doc = docx.Document(file_path)
                        file_content = "\n".join([para.text for para in doc.paragraphs])
                    elif file.filename.lower().endswith('.pdf'):
                        reader = PdfReader(file_path)
                        file_content = "\n".join([page.extract_text() for page in reader.pages])
                    else:
                        continue
                    
                    if file_content.strip():
                        file_contents.append({
                            'filename': file.filename,
                            'content': file_content,
                            'type': 'document'
                        })
                except Exception as e:
                    file_contents.append({
                        'filename': file.filename,
                        'content': f"Error processing file: {str(e)}",
                        'type': 'error'
                    })
                finally:
                    try:
                        os.remove(file_path)
                    except:
                        pass
        elif input_type == 'excel':
            file = request.files.get('file_input')  # Changed to get single file
            if file and file.filename:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
                file.save(file_path)
                
                try:
                    if file.filename.lower().endswith(('.xlsx', '.xls')):
                        df = pd.read_excel(file_path, engine='openpyxl')
                    elif file.filename.lower().endswith('.csv'):
                        df = pd.read_csv(file_path)
                    else:
                        os.remove(file_path)
                        return render_template('index.html', error="Unsupported file format")
                    
                    # Generate summary immediately for Excel
                    summary = abstractive_summary(df.to_string())
                    return render_template('excel_summary.html',
                                        summary=summary,
                                        file_name=file.filename,
                                        file_path=file_path)
                except Exception as e:
                    os.remove(file_path)
                    return render_template('index.html', error=f"Error processing file: {str(e)}")
        elif input_type == 'url':
            url = request.form.get('url_text', '').strip()
            if url:
                try:
                    content = scrape_website(url)
                    file_contents.append({
                        'type': 'url',
                        'content': content,
                        'url': url
                    })
                except Exception as e:
                    file_contents.append({
                        'type': 'url',
                        'content': f"Error scraping website: {str(e)}",
                        'url': url
                    })

        if not file_contents and input_type != 'excel':
            return render_template('index.html', error="No valid input provided")

        if input_type != 'excel':
            return render_template('non_excel_questions.html', 
                               input_type=input_type, 
                               file_contents=file_contents)
    
    except Exception as e:
        return render_template('index.html', error=f"Processing error: {str(e)}")

@app.route('/summarize', methods=['POST'])
def summarize():
    try:
        input_type = request.form.get('input_type')
        
        if input_type == 'excel':
            # Handle Excel file classification
            file_name = request.form.get('file_name')
            file_path = request.form.get('file_path')
            
            if not file_path or not os.path.exists(file_path):
                return render_template('index.html', error="File not found")

            if file_name.lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path, engine='openpyxl')
            elif file_name.lower().endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                return render_template('index.html', error="Unsupported file format")

            if 'complaint' not in df.columns:
                return render_template('index.html', error="File must contain 'complaint' column")

            df = complaint_classifier.classify_complaints(df)
            complaint_classifier.save_department_data(df)
            complaint_classifier.generate_visualizations(df)
            
            dept_counts = df['Department'].value_counts().to_dict()
            churn_reasons = complaint_classifier.churn_prediction_reasons(df)
            complaints_over_time_exists = 'date_of_complaint' in df.columns

            return render_template('excel_result.html',
                                dept_counts=dept_counts,
                                churn_reasons=churn_reasons,
                                complaints_over_time_exists=complaints_over_time_exists,
                                file_name=file_name,
                                file_path=file_path,
                                message="Classification completed successfully")
        else:
            # Original non-Excel summarization logic
            results = []
            i = 0
            while True:
                content_key = f'contents[{i}][content]'
                content = request.form.get(content_key)
                if not content:
                    break
                    
                filename = request.form.get(f'contents[{i}][filename]', '')
                
                summary_length = request.form.get('summary_length', 'medium')
                translate = request.form.get('translate', 'no')
                target_language = request.form.get('target_language', '')
                download_option = request.form.get('download_option', 'no')

                summary = abstractive_summary(content, length=summary_length)
                
                if translate == 'yes' and target_language:
                    try:
                        summary = translator.translate(summary, dest=target_language).text
                    except:
                        summary += "\n\n(Translation failed)"
                
                download_link = None
                if download_option == 'yes':
                    summary_file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"summary_{i}.txt")
                    with open(summary_file_path, "w", encoding="utf-8") as f:
                        f.write(summary)
                    download_link = f"/download_summary/{i}"
                
                results.append({
                    'filename': filename,
                    'summary': summary,
                    'download_link': download_link
                })
                i += 1

            if not results:
                return render_template('index.html', error="No content to summarize")

            return render_template('non_excel_result.html', results=results)
    
    except Exception as e:
        return render_template('index.html', error=f"Summarization error: {str(e)}")

# [Rest of the routes remain the same]

@app.route('/classify', methods=['GET', 'POST'])
def classify():
    if request.method == 'GET':
        file_name = request.args.get('file_name')
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file_name))
    else:
        file_name = request.form.get('file_name')
        file_path = request.form.get('file_path')
    
    if not file_path or not os.path.exists(file_path):
        return render_template('index.html', error="File not found")

    if file_name.lower().endswith(('.xlsx', '.xls')):
        df = pd.read_excel(file_path, engine='openpyxl')
    elif file_name.lower().endswith('.csv'):
        df = pd.read_csv(file_path)
    else:
        return render_template('index.html', error="Unsupported file format")

    if 'complaint' not in df.columns:
        return render_template('index.html', error="File must contain 'complaint' column")

    df = complaint_classifier.classify_complaints(df)
    complaint_classifier.save_department_data(df)
    complaint_classifier.generate_visualizations(df)
    
    dept_counts = df['Department'].value_counts().to_dict()
    churn_reasons = complaint_classifier.churn_prediction_reasons(df)
    complaints_over_time_exists = 'date_of_complaint' in df.columns

    return render_template('excel_result.html',
                        dept_counts=dept_counts,
                        churn_reasons=churn_reasons,
                        complaints_over_time_exists=complaints_over_time_exists,
                        file_name=file_name,
                        file_path=file_path,
                        message="Classification completed successfully")

@app.route('/download_summary/<filename>')
def download_summary(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"summary_{filename}.txt")
    return send_file(filepath, as_attachment=True, download_name=f"summary_{filename}.txt")

@app.route('/static/<path:filename>')
def static_file(filename):
    return send_from_directory('static', filename)

@app.route('/download_department/<department>')
def download_department(department):
    filename = f"{department}_complaints.csv"
    return send_from_directory('static', filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)