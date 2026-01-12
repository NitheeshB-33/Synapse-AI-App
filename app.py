import streamlit as st
from transformers import pipeline
import random
import re
from gtts import gTTS
import io

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
    
    # Ensure we don't try to sample more than we have
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
    
    # Strategy 1: Look for "Definition" sentences (Best Quality)
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

    # Strategy 2: Fallback (If no definitions found, use sentence splitting)
    # This ensures we ALWAYS show something
    if len(flashcards) < 3:
        candidates = [s for s in sentences if len(s) > 40 and len(s) < 120]
        # Shuffle to get variety
        random.shuffle(candidates)
        for sentence in candidates[:5]:
            # Take the first 3-5 words as the "Term" (Concept)
            words = sentence.split()
            if len(words) > 5:
                # Artificial split for flashcard purpose
                term = " ".join(words[:3]) + "..."
                definition = " ".join(words[3:])
                flashcards.append({"term": term, "def": definition})

    # Deduplicate and limit to 6 cards
    unique_cards = list({v['term']: v for v in flashcards}.values())
    return unique_cards[:6]

# ------------------ MAIN INTERFACE ------------------
input_text = st.text_area(
    "📥 Paste your Lecture Notes / Textbook Chapter:", 
    height=250, 
    placeholder="e.g., Photosynthesis is the process used by plants..."
)

if st.button("🚀 Launch Study Mode", type="primary"):
    if len(input_text) < 50:
        st.warning("Please paste more text (at least 50 characters) to generate content.")
    else:
        # Save input to session state to persist across reruns
        st.session_state['input_text'] = input_text
        
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
                    
                    # Store summary in session state for Audio Tab
                    st.session_state['summary_text'] = summary_text
                    
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
                        if st.button(f"Show Answer {i+1}", key=f"ans_{i}"):
                            st.write(f"**Answer:** {q['a']}")
            else:
                st.warning("Could not generate questions. Text might be too short or complex.")

        # --- TAB 3: FLASHCARDS (FIXED) ---
        with tab3:
            st.subheader("Key Terms Extractor")
            cards = generate_flashcards(input_text)
            if cards:
                cols = st.columns(2)
                for i, card in enumerate(cards):
                    with cols[i % 2]:
                        st.info(f"**{card['term'].title()}**")
                        st.write(card['def'])
            else:
                st.warning("Could not extract definitions. Try pasting clearer text.")

        # --- TAB 4: AUDIO NOTEBOOK (FIXED) ---
        with tab4:
            st.subheader("🎧 Listen to your Notes")
            if 'summary_text' in st.session_state:
                text_to_speak = st.session_state['summary_text']
                
                if st.button("🔊 Generate Audio Podcast"):
                    with st.spinner("Synthesizing speech..."):
                        try:
                            # Use memory buffer instead of saving to file (Fixes Cloud Issues)
                            sound_file = io.BytesIO()
                            tts = gTTS(text_to_speak, lang='en')
                            tts.write_to_fp(sound_file)
                            st.audio(sound_file)
                            st.success("Playing Audio...")
                        except Exception as e:
                            st.error(f"Audio Generation Error: {e}")
            else:
                st.info("💡 Tip: A summary will be generated automatically in Tab 1 first.")

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
