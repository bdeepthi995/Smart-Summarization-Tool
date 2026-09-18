# AI-Based Automated Text Summarization Tool
An AI-powered web application that generates summaries from different types of input such as text, PDF, DOCX, TXT, Excel/CSV files, and URLs.

## Features
* Text summarization using BART
* Summarization of PDF, DOCX, and TXT files
* Excel/CSV file processing
* URL content summarization
* Different summary lengths
* Translation support
* Complaint classification and analysis
* Churn prediction analysis
* Download generated summaries

## Technologies Used
* Python
* Flask
* BART (facebook/bart-large-cnn)
* Pandas
* Scikit-learn
* NLTK
* HTML
* CSS
* JavaScript
* MySQL

## How to Run
1. Install the required Python libraries.
   pip install flask transformers torch googletrans==4.0.0-rc1 python-docx pandas openpyxl PyPDF2 requests beautifulsoup4 matplotlib scikit-learn nltk
2. Run the application.
   python app.py
3. Open the application in your browser:
   http://127.0.0.1:5000/

## Project Structure
AI-Based-Automated-Text-Summarization-Tool/
│
├── app.py
├── complaint_classifier.py
│
├── templates/
│   ├── index.html
│   ├── excel_result.html
│   ├── excel_summary.html
│   ├── non_excel_questions.html
│   └── non_excel_result.html
│
└── static/
    ├── script.js
    └── styles.css

## Project Purpose
The project is designed to reduce the time required to read and understand large amounts of information by automatically extracting and generating concise summaries from multiple sources and file formats.
