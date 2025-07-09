# Resume Analyzer Chatbot

A Django-based web application that analyzes resumes and provides interactive chat functionality with ATS (Applicant Tracking System) scoring features.

## Features

- Resume analysis and parsing
- Interactive Q&A about resumes
- Job Description compatibility scoring
- ATS optimization suggestions
- Chat session history
- Responsive web interface

## Prerequisites

- Python 3.8+
- MySQL 5.7+
- Google Gemini API key

## Installation

1. Clone the repository:
   git clone https://github.com/yourusername/resume-analyzer.git
   cd resume-analyzer

2. Create and activate a virtual environment
3. Install dependencies
        pip install -r requirements.txt

4. Edit .env with your configuration
        DB_NAME=resume_analyzer
        DB_USER=your_db_user
        DB_PASSWORD=your_db_password
        DB_HOST=localhost
        DB_PORT=3306
        GEMINI_API_KEY=your-google-gemini-api-key

5. Set up MySQL database
        CREATE DATABASE resume_analyzer CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

6. Run migrations 
        python manage.py migrate

7. Run the development server
        python manage.py runserver

API Endpoints:
http://127.0.0.1:8000/api/ (Upload Your Resume)

http://127.0.0.1:8000/api/chat/<Resume_id> (Start Converstaion with Chatbot)
