import streamlit as st
import re
from typing import Dict, List
from youtube_transcript_api import YouTubeTranscriptApi
from llm import answer
import time

# Set up page configuration
st.set_page_config(
    page_title="YouTube Summary Generator",
    page_icon="📝",
    layout="wide"
)

# Apply custom CSS with animations
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
    
    * {font-family: 'Roboto', sans-serif;}
    
    .main {
        padding: 2rem;
        max-width: 1200px;
        margin: 0 auto;
    }
    
    .stButton>button {
        width: 100%;
        background-color: #FF0000;
        color: white;
        border: none;
        padding: 0.6rem 0;
        font-weight: 500;
        border-radius: 30px;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #D00000;
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    h1, h2, h3 {
        color: #212121;
    }
    
    .stTextInput>div>div>input {
        border-radius: 10px;
    }
    
    .youtube-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        border-left: 5px solid #FF0000;
        animation: fadeIn 0.8s ease;
    }
    
    .summary-card {
        background-color: #f9f9f9;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-top: 1.5rem;
        border-left: 5px solid #4285F4;
        animation: slideUp 0.8s ease;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes slideUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    .pulse {
        animation: pulse 2s infinite;
    }
    
    .language-selector {
        background-color: white;
        border-radius: 10px;
        padding: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .header-container {
        display: flex;
        align-items: center;
        margin-bottom: 2rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid #eee;
    }
    
    .app-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
        background: linear-gradient(90deg, #FF0000, #FF5252);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    </style>
    """, unsafe_allow_html=True)

# Helper functions (same as before)
def extract_video_id(url: str) -> str:
    """Extract the video ID from a YouTube URL."""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:shorts\/)([0-9A-Za-z_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return ""

def get_youtube_transcript(video_id: str) -> List[Dict]:
    """Get the transcript of a YouTube video."""
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return transcript
    except Exception as e:
        st.error(f"Error fetching transcript: {str(e)}")
        return []

def format_time(seconds: float) -> str:
    """Format time in seconds to hh:mm:ss format."""
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def generate_summary(transcript: List[Dict], language: str) -> str:
    """Generate basic summary using LLM API."""
    transcript_text = "\n".join([f"{format_time(float(entry['start']))}: {entry['text']}" for entry in transcript])

    system_prompt = "You are a helpful assistant that creates summaries of YouTube videos from transcripts."
    user_prompt = f"""
    Please analyze the following YouTube video transcript and create a comprehensive summary.
    The summary should capture the main points and key information from the video.
    
    Language for the summary: {language}
    
    Here's the transcript:
    {transcript_text}
    """
    st.session_state.prompt = user_prompt

    try:
        # Animated loading simulation
        with st.spinner("🧠 Analyzing transcript..."):
            # Call the answer function from llm.py
            summary_text = answer(system_prompt, user_prompt, "github")
            # Add slight delay for transition effect
            time.sleep(0.5)
            
        st.session_state.llm_output = summary_text
        return summary_text
    except Exception as e:
        st.error(f"Error generating summary: {str(e)}")
        return ""

# Main app
def main():
    # Custom header with animation
    st.markdown('<div class="header-container"><h1 class="app-title">✨ YouTube Summary Generator</h1></div>', unsafe_allow_html=True)
    
    # Intro text with animation
    st.markdown("""
    <div style="animation: fadeIn 1s ease;">
        <p>Get instant summaries of any YouTube video with just one click. 
        Enter a YouTube URL below and select your preferred language.</p>
    </div>
    """, unsafe_allow_html=True)

    # Session state initialization
    if 'summary' not in st.session_state:
        st.session_state.summary = ""
    if 'prompt' not in st.session_state:
        st.session_state.prompt = ""
    if 'llm_output' not in st.session_state:
        st.session_state.llm_output = ""

    # Input section with card styling
    st.markdown('### 🎬 Enter YouTube Video')
    
    col1, col2 = st.columns([3, 1])

    with col1:
        youtube_url = st.text_input("", placeholder="Paste YouTube URL here...", key="youtube_url")

    with col2:
        languages = {
            "en": "🇬🇧 English",
            "zh-TW": "🇹🇼 Traditional Chinese",
            "zh-CN": "🇨🇳 Simplified Chinese",
            "fr": "🇫🇷 French",
            "es": "🇪🇸 Spanish",
            "ja": "🇯🇵 Japanese"
        }
        language = st.selectbox("Summary Language", options=list(languages.keys()), format_func=lambda x: languages[x])
        st.markdown('</div>', unsafe_allow_html=True)

    # Generate summary button with animation
    if st.button("✨ Generate Summary"):
        if youtube_url:
            # Progress animation
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Animated progress simulation
            status_text.text("Extracting video ID...")
            progress_bar.progress(10)
            time.sleep(0.3)
            
            video_id = extract_video_id(youtube_url)
            
            if video_id:
                # Update progress
                status_text.text("Getting transcript...")
                progress_bar.progress(30)
                time.sleep(0.3)
                
                # Get transcript
                transcript = get_youtube_transcript(video_id)
                
                if transcript:
                    # Update progress
                    status_text.text("Generating summary...")
                    progress_bar.progress(60)
                    
                    # Generate summary
                    summary = generate_summary(transcript, language)
                    
                    # Update progress
                    progress_bar.progress(100)
                    status_text.empty()
                    progress_bar.empty()
                    
                    if summary:
                        st.session_state.summary = summary
                        st.success("✅ Summary generated successfully!")
                    else:
                        st.error("Failed to generate summary.")
                else:
                    progress_bar.empty()
                    status_text.empty()
                    st.error("Failed to get transcript. The video might not have subtitles or captions.")
            else:
                progress_bar.empty()
                status_text.empty()
                st.error("Invalid YouTube URL. Please check and try again.")
        else:
            st.warning("Please enter a YouTube URL.")
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close the card div

    # Display summary with card styling and animation
    if st.session_state.summary:
        st.markdown('### 📋 Video Summary')
        st.markdown(st.session_state.summary)
        st.markdown('</div>', unsafe_allow_html=True)

    # Display debug information in a cleaner way
    with st.expander("🔍 Debug Information"):
        tabs = st.tabs(["Prompt", "LLM Output"])
        
        with tabs[0]:
            st.text_area("", value=st.session_state.prompt, height=200, disabled=True, key="prompt_textarea")
            
        with tabs[1]:
            st.text_area("", value=st.session_state.llm_output, height=200, disabled=True, key="llm_output_textarea")

    # Footer
    st.markdown("""
    <div style="text-align: center; margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #eee; animation: fadeIn 2s ease;">
        <p style="color: #666; font-size: 0.8rem;">Made with ❤️ using Streamlit and AI</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
