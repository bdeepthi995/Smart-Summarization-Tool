import pandas as pd
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
from sklearn.metrics import classification_report

class ComplaintClassifier:
    def __init__(self):
        # Define department keywords for keyword-based classification
        self.department_keywords = {
            'Customer Support': ['help', 'support', 'assist', 'service', 'issue', 'call', 'query'],
            'Technical Issues': ['error', 'bug', 'problem', 'crash', 'malfunction', 'fail', 'glitch'],
            'Billing & Payment': ['charge', 'billing', 'payment', 'invoice', 'transaction', 'amount', 'pay'],
            'General Feedback': ['feedback', 'suggestion', 'idea', 'general', 'recommendation', 'comment'],
            'Others': ['miscellaneous', 'unknown', 'query', 'general', 'other']
        }
        
        # Initialize the ML model (will be trained when needed)
        self.model = None

    def classify_department(self, complaint):
        """Classifies complaint into one of the departments based on keywords."""
        for dept, keywords in self.department_keywords.items():
            for keyword in keywords:
                if keyword.lower() in complaint.lower():
                    return dept
        return 'Others'

    def save_department_data(self, data):
        """Saves data for each department into individual CSV files"""
        for department in data['Department'].unique():
            department_data = data[data['Department'] == department]
            department_data.to_csv(f'static/{department}_complaints.csv', index=False)

    def generate_visualizations(self, data):
        """Generates visualizations for complaints analysis"""
        # Complaints per Department (Bar chart)
        dept_counts = data['Department'].value_counts()
        plt.figure(figsize=(6, 6))
        dept_counts.plot(kind='bar', color='skyblue')
        plt.title('Complaints per Department')
        plt.xlabel('Department')
        plt.ylabel('Complaint Count')
        plt.savefig('static/complaints_per_department.png')
        plt.close()

        # Complaints Over Time (Line chart)
        if 'date_of_complaint' in data.columns:
            data['date_of_complaint'] = pd.to_datetime(data['date_of_complaint'])
            complaints_over_time = data.groupby(data['date_of_complaint'].dt.to_period('M')).size()
            plt.figure(figsize=(6, 6))
            complaints_over_time.plot(kind='line', color='green')
            plt.title('Complaints Over Time')
            plt.xlabel('Date')
            plt.ylabel('Number of Complaints')
            plt.savefig('static/complaints_over_time.png')
            plt.close()

    def churn_prediction_reasons(self, data):
        """Provides reasons for churn predictions based on department intent"""
        churn_reasons = []
        dept_complaints = data['Department'].value_counts()

        for dept, count in dept_complaints.items():
            if dept == 'Customer Support' and count > 5:
                churn_reasons.append(f"High complaint count in {dept}: May indicate unresolved issues or dissatisfaction.")
            elif dept == 'Technical Issues' and count > 5:
                churn_reasons.append(f"High complaint count in {dept}: Likely to indicate dissatisfaction with the technical product.")
            elif dept == 'Billing & Payment' and count > 5:
                churn_reasons.append(f"High complaint count in {dept}: May indicate payment or billing issues affecting customer trust.")
            elif dept == 'General Feedback' and count > 5:
                churn_reasons.append(f"High complaint count in {dept}: May reflect dissatisfaction with general services or features.")
            elif dept == 'Technical Feedback' and count > 5:
                churn_reasons.append(f"High complaint count in {dept}: Likely dissatisfaction with technical aspects or product development.")
            else:
                churn_reasons.append(f"Low complaint count in {dept}: No immediate churn risk.")
        
        return churn_reasons

    def train_classifier(self, df):
        """
        Trains a text classification model using the dataset.
        Assumes the dataset has 'complaint' and 'Department' columns.
        """
        # Split the data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(
            df['complaint'], df['Department'], test_size=0.2, random_state=42)
        
        # Create a pipeline with TF-IDF vectorizer and Naive Bayes classifier
        self.model = make_pipeline(TfidfVectorizer(), MultinomialNB())
        
        # Train the model
        self.model.fit(X_train, y_train)
        
        # Evaluate the model
        y_pred = self.model.predict(X_test)
        print(classification_report(y_test, y_pred))
    
    def classify_complaints(self, df):
        """
        Classifies complaints using either the trained model or keyword-based approach.
        Returns the dataframe with added 'Department' column.
        """
        if 'Department' in df.columns and self.model is None:
            # If we have labeled data but no model trained yet
            self.train_classifier(df)
        
        if self.model is not None:
            # Use the trained model if available
            df['Department'] = self.model.predict(df['complaint'])
        else:
            # Fall back to keyword-based classification
            df['Department'] = df['complaint'].apply(self.classify_department)
        
        return df