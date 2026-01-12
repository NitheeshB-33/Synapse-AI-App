🧠 Synapse AI: Intelligent Study Companion

Synapse AI is an educational technology tool designed to help students learn faster and retain information better. It solves the problem of "information overload" by using Artificial Intelligence to summarize long lecture notes and automatically generate practice quizzes for active recall.

(Built for the IBM SkillsBuild AI Internship)

🔗 Live Demo

Click Here to Launch Synapse AI

📖 Problem Statement

Students often struggle to digest complex textbook chapters and lecture notes. Searching for summaries online yields generic results that don't match specific curriculums. There is a need for a tool that can process specific student notes and convert them into study aids instantly.

🚀 Key Features

AI Summarization: Uses the DistilBART Transformer (sshleifer/distilbart-cnn-12-6) to compress text by 50-60% while retaining critical concepts.

Automated Quiz Generator: A logic-based engine that converts input text into "Fill-in-the-Blank" questions, enabling students to test themselves immediately.

Subject Agnostic: Works for History, Science, Literature, or Technical subjects.

🛠️ Technical Stack

Language: Python 3.9+

Interface: Streamlit

AI Model: Hugging Face Transformers

Logic: Python Regex & Randomization

📦 Installation

Clone the repository:

git clone [https://github.com/your-username/synapse-ai.git](https://github.com/your-username/synapse-ai.git)


Install dependencies:

pip install -r requirements.txt


Run the application:

streamlit run app.py


📄 License

MIT License
