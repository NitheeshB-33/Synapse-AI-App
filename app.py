import streamlit as st
from transformers import pipeline
import random
import re
from gtts import gTTS
import io

# ------------------ UI CONFIGURATION ------------------
st.set_page_config(
    page_title="NotesGenie | Study Suite",
    page_icon="🧞",
    layout="wide"
)

# ------------------ HEADER ------------------
st.title("🧞 NotesGenie")
st.markdown("### Your Magical Study Companion")
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
    
    count = min(len(candidates), 5)
    if count == 0: return []
    
    selected = random.sample(candidates, count)
    
    for sentence in selected:
        words = sentence.split()
        long_words = [w for w in words if len(w) > 4]
        if long_words:
            keyword = random.choice(long_words)
            # Remove punctuation from answer
            answer = re.sub(r'[^\w\s]', '', keyword)
            question = sentence.replace(keyword, "__________")
            quiz_data.append({"q": question, "a": answer})
    return quiz_data

def generate_flashcards(text):
    sentences = re.split(r'(?<=[.!?]) +', text)
    flashcards = []
    
    # Strategy 1: Definition Extraction
    for sentence in sentences:
        if " is " in sentence or " are " in sentence or " refers to " in sentence:
            parts = sentence.split(" is ", 1)
            if len(parts) < 2: parts = sentence.split(" are ", 1)
            if len(parts) < 2: parts = sentence.split(" refers to ", 1)
            
            if len(parts) == 2:
                term = parts[0].strip()
                definition = parts[1].strip()
                if len(term.split()) <= 6 and len(definition) > 10:
                    flashcards.append({"term": term, "def": definition})

    # Strategy 2: Fallback
    if len(flashcards) < 3:
        candidates = [s for s in sentences if len(s) > 40 and len(s) < 120]
        random.shuffle(candidates)
        for sentence in candidates[:5]:
            words = sentence.split()
            if len(words) > 5:
                term = " ".join(words[:3]) + "..."
                definition = " ".join(words[3:])
                flashcards.append({"term": term, "def": definition})

    unique_cards = list({v['term']: v for v in flashcards}.values())
    return unique_cards[:6]

# ------------------ MAIN INTERFACE ------------------
input_text = st.text_area(
    "📥 Paste your Lecture Notes / Textbook Chapter:", 
    height=250, 
    placeholder="e.g., Artificial Intelligence is the simulation of human intelligence processes by machines..."
)

# Initialize Session State
if 'generated' not in st.session_state:
    st.session_state['generated'] = False
if 'summary' not in st.session_state:
    st.session_state['summary'] = ""
if 'quiz_data' not in st.session_state:
    st.session_state['quiz_data'] = []
if 'flashcards' not in st.session_state:
    st.session_state['flashcards'] = []
if 'audio_file' not in st.session_state:
    st.session_state['audio_file'] = None

if st.button("🚀 Grant My Wish (Process)", type="primary"):
    if len(input_text) < 50:
        st.warning("Please paste more text (at least 50 characters).")
    else:
        with st.spinner("NotesGenie is working its magic..."):
            # 1. Generate Summary
            try:
                summarizer = load_summarizer()
                input_len = len(input_text.split())
                max_len = max(30, int(input_len * 0.5))
                min_len = max(10, int(input_len * 0.2))
                
                summary = summarizer(input_text, max_length=max_len, min_length=min_len, do_sample=False)
                st.session_state['summary'] = summary[0]['summary_text']
            except Exception as e:
                st.error(f"Summarization Error: {e}")

            # 2. Generate Quiz
            st.session_state['quiz_data'] = generate_quiz(input_text)
            
            # 3. Generate Flashcards
            st.session_state['flashcards'] = generate_flashcards(input_text)
            
            # 4. Reset Audio
            st.session_state['audio_file'] = None
            
            # Mark as generated
            st.session_state['generated'] = True

# --- DISPLAY TABS ---
if st.session_state['generated']:
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Summary", "❓ Quiz", "📇 Flashcards", "🎧 Audio Note"])

    # --- TAB 1: SUMMARY ---
    with tab1:
        st.success("Summary Generated")
        st.info(st.session_state['summary'])

    # --- TAB 2: QUIZ ---
    with tab2:
        st.subheader("Knowledge Check")
        if st.session_state['quiz_data']:
            for i, q in enumerate(st.session_state['quiz_data']):
                st.markdown(f"**Q{i+1}: {q['q']}**")
                with st.expander(f"Show Answer {i+1}"):
                    st.success(f"**Answer:** {q['a']}")
        else:
            st.warning("Could not generate questions. Text might be too short.")

    # --- TAB 3: FLASHCARDS ---
    with tab3:
        st.subheader("Key Terms")
        if st.session_state['flashcards']:
            cols = st.columns(2)
            for i, card in enumerate(st.session_state['flashcards']):
                with cols[i % 2]:
                    st.info(f"**{card['term'].title()}**")
                    st.write(card['def'])
        else:
            st.warning("No flashcards could be generated.")

    # --- TAB 4: AUDIO NOTEBOOK ---
    with tab4:
        st.subheader("🎧 Listen to your Notes")
        
        if st.button("🔊 Generate Audio Podcast"):
            with st.spinner("Synthesizing speech..."):
                try:
                    text_to_speak = st.session_state['summary']
                    
                    # Clean text to remove symbols that break the API
                    clean_text = re.sub(r'[^\w\s.,?!]', '', text_to_speak)
                    
                    if clean_text:
                        # Use 'co.uk' TLD to bypass Google's rate limiting on .com
                        tts = gTTS(clean_text, lang='en', tld='co.uk')
                        
                        # Save to a temporary file
                        audio_path = "audio_summary.mp3"
                        tts.save(audio_path)
                        
                        # Read file into session state
                        with open(audio_path, "rb") as f:
                            st.session_state['audio_file'] = f.read()
                            
                        st.success("Audio Ready! Press Play below.")
                    else:
                        st.warning("Summary text is empty or invalid.")
                        
                except Exception as e:
                    st.error(f"Audio Error: {e}. Try generating again in a few seconds.")

        # Persistent Audio Player
        if st.session_state['audio_file']:
            st.audio(st.session_state['audio_file'], format='audio/mp3')

# ------------------ SIDEBAR ------------------
with st.sidebar:
    st.markdown("### 📊 Study Stats")
    if input_text:
        st.metric("Word Count", len(input_text.split()))
    st.markdown("---")
    st.caption("NotesGenie © 2026")
