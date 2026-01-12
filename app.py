import streamlit as st
from transformers import pipeline
import random
import re
from gtts import gTTS
import io

# ------------------ UI CONFIGURATION ------------------
st.set_page_config(
    page_title="NotesGenie | Study Suite",
    page_icon="🧠",
    layout="wide"
)

# ------------------ HEADER ------------------
st.title("NotesGenie")
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
    
    count = min(len(candidates), 5)
    if count == 0: return []
    
    selected = random.sample(candidates, count)
    
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
    placeholder="e.g., Photosynthesis is the process used by plants..."
)

# Initialize Session State variables if they don't exist
if 'generated' not in st.session_state:
    st.session_state['generated'] = False
if 'summary' not in st.session_state:
    st.session_state['summary'] = ""
if 'quiz_data' not in st.session_state:
    st.session_state['quiz_data'] = []
if 'flashcards' not in st.session_state:
    st.session_state['flashcards'] = []
if 'audio_bytes' not in st.session_state:
    st.session_state['audio_bytes'] = None

if st.button("🚀 Launch Study Mode", type="primary"):
    if len(input_text) < 50:
        st.warning("Please paste more text (at least 50 characters).")
    else:
        with st.spinner("Processing content..."):
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
            st.session_state['audio_bytes'] = None
            
            # Mark as generated to show tabs
            st.session_state['generated'] = True

# --- DISPLAY TABS (Only if content is generated) ---
if st.session_state['generated']:
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Summary", "❓ Quiz", "📇 Flashcards", "🎧 Audio Note"])

    # --- TAB 1: SUMMARY ---
    with tab1:
        st.success("Abstract Generated")
        st.info(st.session_state['summary'])

    # --- TAB 2: QUIZ (FIXED) ---
    with tab2:
        st.subheader("Knowledge Check")
        if st.session_state['quiz_data']:
            for i, q in enumerate(st.session_state['quiz_data']):
                st.markdown(f"**Q{i+1}: {q['q']}**")
                # Using expander instead of button prevents reload issues
                with st.expander(f"Show Answer {i+1}"):
                    st.success(f"**Answer:** {q['a']}")
        else:
            st.warning("Could not generate questions. Text might be too short.")

    # --- TAB 3: FLASHCARDS ---
    with tab3:
        st.subheader("Key Terms Extractor")
        if st.session_state['flashcards']:
            cols = st.columns(2)
            for i, card in enumerate(st.session_state['flashcards']):
                with cols[i % 2]:
                    st.info(f"**{card['term'].title()}**")
                    st.write(card['def'])
        else:
            st.warning("No flashcards could be generated.")

    # --- TAB 4: AUDIO NOTEBOOK (FIXED) ---
    with tab4:
        st.subheader("🎧 Listen to your Notes")
        
        # Button to trigger generation
        if st.button("🔊 Generate Audio Podcast"):
            with st.spinner("Synthesizing speech..."):
                try:
                    text_to_speak = st.session_state['summary']
                    if text_to_speak:
                        sound_file = io.BytesIO()
                        tts = gTTS(text_to_speak, lang='en')
                        tts.write_to_fp(sound_file)
                        sound_file.seek(0) # Important: reset pointer to start of file
                        st.session_state['audio_bytes'] = sound_file
                    else:
                        st.warning("No summary available to read.")
                except Exception as e:
                    st.error(f"Audio Error: {e}")

        # Persistent Audio Player
        if st.session_state['audio_bytes']:
            st.audio(st.session_state['audio_bytes'], format='audio/mp3')

# ------------------ SIDEBAR ------------------
with st.sidebar:
    st.markdown("### 📊 Study Stats")
    if input_text:
        st.metric("Word Count", len(input_text.split()))
    st.markdown("---")
    st.caption("NotesGenie © 2026")
