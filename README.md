NUTRIMATE

🥗 AI-Based Nutrition Planner

An AI-powered web application that provides personalized meal and nutrition recommendations based on user input such as age, gender, weight, height, activity level, and dietary goals (e.g., weight loss, weight gain, or maintenance). Built with a frontend using HTML, CSS, JavaScript and a Python backend (Flask) integrated with a machine learning model.

🚀 Features

🧠 AI-driven meal recommendations

🔍 Nutrient and calorie estimation

📊 Visual nutrient breakdown using charts

🧾 Personalized dietary plans

🔗 API-based architecture for easy integration

🌐 Responsive web interface


🛠️ Tech Stack

Frontend

HTML5

CSS3

JavaScript (Fetch API)

Backend

Python 3

Flask

Pandas, Scikit-learn

Nutrition Dataset (Kaggle/USDA)

Optional

Chart.js (for nutrient graphs)

SQLite or Firebase (for user data storage)

🧪 How It Works

User enters their profile (age, gender, weight, height, activity level, goal).

Frontend sends this data to the backend using JavaScript Fetch API.

Flask backend receives the data and runs a trained ML model to:

Estimate daily calorie requirement

Recommend a list of meals matching the dietary goal

The response is displayed on the frontend dynamically with nutrition breakdown.

🧠 AI/ML Functionality

Trained a simple Decision Tree / KNN model using a nutrition dataset (foods, calories, macronutrients).

Features considered: Age, gender, BMI, activity level, and goal.

Labels: Meal clusters optimized for goal (e.g., weight loss meals, high-protein meals).

⚠️ API Key Note

🔐 IMPORTANT: If you use any external API (e.g., Gemini, Firebase, or nutrition APIs), make sure you replace the actual API key with "YOUR-API-KEY" in the public code before uploading to GitHub.

Never commit sensitive credentials to a public repository.

📦 Installation

Clone the repository:

git clone https://github.com/gujeet3010/NutriMate.git
cd NutriMate
Create a virtual environment and activate it:

python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
Install dependencies:

pip install -r requirements.txt
Run the Flask app:

python app.py
Visit http://localhost:5000 in your browser.

🙋‍♂️ Contributors

Gurjeet Kaur (Team Lead & ML model trainer)

Namrata Jain (Frontend Developer)

Aditya Sharma (API & Backend Integration)

💬 Feedback

If you have suggestions or issues, please open an issue or submit a pull request. Your feedback helps improve the project!
