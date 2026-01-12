import streamlit as st
from transformers import pipeline
import random
import re
from gtts import gTTS
import os

# ------------------ UI CONFIGURATION ------------------
st.set_page_config(
    page_title="Synapse AI | Study Suite",
    page_icon="🧠",
    layout="wide"
)

# ------------------ HEADER ------------------
st.title("🧠 Synapse AI")
st.markdown("### The Ultimate Study Companion")
st.caption("Summarize • Quiz • Flashcards • Audio Notes")
st.markdown("---")

# ------------------ LOAD AI MODELS ------------------
@st.cache_resource
def load_summarizer():
    return pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

# ------------------ LOGIC FUNCTIONS ------------------
def generate_quiz(text):
    sentences = re.split(r'(?<=[.!?]) +', text)
    quiz_data = []
    candidates = [s for s in sentences if len(s) > 30 and len(s) < 150]
    selected = random.sample(candidates, min(len(candidates), 5))
    
    for sentence in selected:
        words = sentence.split()
        long_words = [w for w in words if len(w) > 4]
        if long_words:
            keyword = random.choice(long_words)
            answer = re.sub(r'[^\w\s]', '', keyword)
            question = sentence.replace(keyword, "__________")
            quiz_data.append({"q": question, "a": answer})
    return quiz_data

def generate_flashcards(text):
    # Logic: Look for sentences that define something (e.g., "X is Y")
    sentences = re.split(r'(?<=[.!?]) +', text)
    flashcards = []
    
    for sentence in sentences:
        # Simple heuristic: Sentences with "is a", "refers to", "defined as"
        if " is " in sentence or " are " in sentence:
            parts = sentence.split(" is ", 1)
            if len(parts) < 2: parts = sentence.split(" are ", 1)
            
            if len(parts) == 2:
                term = parts[0].strip()
                definition = parts[1].strip()
                # Keep terms short (max 5 words) to ensure they are actually terms
                if len(term.split()) <= 5 and len(definition) > 10:
                    flashcards.append({"term": term, "def": definition})
    
    return list(dict((v['term'], v) for v in flashcards).values())[:6] # Dedup and limit

# ------------------ MAIN INTERFACE ------------------
input_text = st.text_area(
    "📥 Paste your Lecture Notes / Textbook Chapter:", 
    height=250, 
    placeholder="e.g., Photosynthesis is the process used by plants..."
)

if st.button("🚀 Launch Study Mode", type="primary"):
    if len(input_text) < 50:
        st.warning("Please paste more text to generate content.")
    else:
        # Create Tabs for different features
        tab1, tab2, tab3, tab4 = st.tabs(["📝 Summary", "❓ Quiz", "📇 Flashcards", "🎧 Audio Note"])
        
        # --- TAB 1: SUMMARY ---
        with tab1:
            with st.spinner("Analyzing text..."):
                try:
                    summarizer = load_summarizer()
                    input_len = len(input_text.split())
                    max_len = max(30, int(input_len * 0.5))
                    min_len = max(10, int(input_len * 0.2))
                    
                    summary = summarizer(input_text, max_length=max_len, min_length=min_len, do_sample=False)
                    summary_text = summary[0]['summary_text']
                    
                    st.success("Abstract Generated")
                    st.info(summary_text)
                    st.caption(f"Compressed from {input_len} words to {len(summary_text.split())} words.")
                    
                    # Save summary for audio tab
                    st.session_state['summary_cache'] = summary_text
                    
                except Exception as e:
                    st.error(f"Error: {e}")

        # --- TAB 2: QUIZ ---
        with tab2:
            st.subheader("Knowledge Check")
            quiz = generate_quiz(input_text)
            if quiz:
                for i, q in enumerate(quiz):
                    with st.expander(f"Question {i+1}"):
                        st.write(q['q'])
                        if st.button(f"Show Answer {i+1}"):
                            st.write(f"**Answer:** {q['a']}")
            else:
                st.warning("Text too short for quiz generation.")

        # --- TAB 3: FLASHCARDS (NEW!) ---
        with tab3:
            st.subheader("Key Terms Extractor")
            cards = generate_flashcards(input_text)
            if cards:
                cols = st.columns(2)
                for i, card in enumerate(cards):
                    with cols[i % 2]:
                        st.info(f"**{card['term'].title()}**")
                        st.caption(card['def'])
            else:
                st.warning("No specific definitions found in the text.")

        # --- TAB 4: AUDIO NOTEBOOK (NEW!) ---
        with tab4:
            st.subheader("🎧 Listen to your Notes")
            if 'summary_cache' in st.session_state:
                text_to_speak = st.session_state['summary_cache']
                if st.button("🔊 Generate Audio Podcast"):
                    with st.spinner("Synthesizing speech..."):
                        tts = gTTS(text_to_speak, lang='en')
                        tts.save("audio_summary.mp3")
                        st.audio("audio_summary.mp3")
                        st.success("Ready to play!")
            else:
                st.warning("Please generate a summary in Tab 1 first.")

# ------------------ SIDEBAR ------------------
with st.sidebar:
    st.markdown("### 📊 Study Stats")
    if input_text:
        st.metric("Word Count", len(input_text.split()))
        st.metric("Est. Read Time", f"{round(len(input_text.split())/200, 1)} mins")
    else:
        st.info("Paste text to see stats.")
        
    st.markdown("---")
    st.caption("Synapse AI © 2026")
