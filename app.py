import streamlit as st
from transformers import pipeline
import random
import re

# ------------------ UI CONFIGURATION ------------------
st.set_page_config(
    page_title="Synapse AI | Study Companion",
    page_icon="🧠",
    layout="wide"
)

# ------------------ HEADER ------------------
st.title("🧠 Synapse AI")
st.subheader("Intelligent Study Companion for Students")
st.markdown("---")

# ------------------ SIDEBAR ------------------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/learning.png")
    st.markdown("### ⚙️ Study Toolkit")
    mode = st.radio("Select Mode:", ["📝 Notes Summarizer", "❓ Quiz Generator"])
    
    st.info("""
    **How it works:**
    1. Paste your lecture notes.
    2. AI summarizes key points.
    3. AI generates practice questions.
    """)
    st.caption("Built for IBM SkillsBuild Internship")

# ------------------ LOAD AI MODELS ------------------
@st.cache_resource
def load_summarizer():
    # Load a lightweight, fast summarization model
    return pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

# ------------------ QUIZ LOGIC (Rule-Based) ------------------
def generate_quiz(text):
    # Split text into sentences using regex (split by . ! ?)
    sentences = re.split(r'(?<=[.!?]) +', text)
    quiz_data = []
    
    # Filter for good length sentences (not too short, not too long)
    candidates = [s for s in sentences if len(s) > 30 and len(s) < 150]
    
    # Pick up to 5 random sentences
    selected = random.sample(candidates, min(len(candidates), 5))
    
    for sentence in selected:
        words = sentence.split()
        # Find words suitable for blanks (longer than 4 chars)
        long_words = [w for w in words if len(w) > 4]
        
        if long_words:
            keyword = random.choice(long_words)
            # Clean keyword of punctuation for the answer key
            answer = re.sub(r'[^\w\s]', '', keyword)
            
            # Create question with blank
            question = sentence.replace(keyword, "__________")
            quiz_data.append({"q": question, "a": answer})
            
    return quiz_data

# ------------------ MAIN INTERFACE ------------------
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📥 Input Study Material")
    input_text = st.text_area(
        "Paste your lecture notes or textbook content here:", 
        height=400, 
        placeholder="e.g., Photosynthesis is the process used by plants to convert light energy into chemical energy..."
    )

with col2:
    st.markdown("### 🤖 AI Output")
    
    if st.button("🚀 Process Content", type="primary"):
        if len(input_text) < 50:
            st.warning("Please paste at least 50 characters of text.")
        else:
            # --- MODE 1: SUMMARIZER ---
            if mode == "📝 Notes Summarizer":
                with st.spinner("Compressing knowledge..."):
                    try:
                        summarizer = load_summarizer()
                        # Calculate lengths dynamically based on input length
                        input_len = len(input_text.split())
                        max_len = max(30, int(input_len * 0.5)) 
                        min_len = max(10, int(input_len * 0.2))
                        
                        summary = summarizer(input_text, max_length=max_len, min_length=min_len, do_sample=False)
                        result_text = summary[0]['summary_text']
                        
                        st.success("Summary Generated!")
                        st.markdown(f"> {result_text}")
                        st.caption(f"Reduced word count by ~{100 - int(len(result_text)/len(input_text)*100)}%")
                        
                    except Exception as e:
                        st.error(f"Error during summarization: {e}")

            # --- MODE 2: QUIZ GENERATOR ---
            elif mode == "❓ Quiz Generator":
                with st.spinner("Drafting questions..."):
                    quiz_questions = generate_quiz(input_text)
                    
                    if quiz_questions:
                        st.success(f"Generated {len(quiz_questions)} Practice Questions")
                        for i, item in enumerate(quiz_questions):
                            with st.expander(f"Question {i+1}"):
                                st.write(f"**{item['q']}**")
                                st.write(f"*(Answer: {item['a']})*")
                    else:
                        st.warning("Text too short to generate questions. Please add more content.")

# ------------------ FOOTER ------------------
st.markdown("---")
st.markdown("© 2026 Synapse AI | Automated Study Assistant")
