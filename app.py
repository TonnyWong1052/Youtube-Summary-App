import streamlit as st
import re
import json
from typing import Dict, List
from youtube_transcript_api import YouTubeTranscriptApi
from llm import answer
import time
import requests

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

def get_youtube_transcript(language_code: str, video_id: str) -> List[Dict]:
    """Get the transcript of a YouTube video."""
    try:
        # First attempt with YouTubeTranscriptApi
        raise Exception("Testing error handling")
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return transcript
    except Exception as e:
        # st.warning(f"YouTube Transcript API error: {str(e)}. Trying alternative API...")
        
        # Fallback to alternative API
        try:
            fallback_url = f"https://yt.vl.comp.polyu.edu.hk/transcript?language_code={language_code}&password=for_demo&video_id={video_id}"
            response = requests.get(fallback_url)
            
            if response.status_code == 200:
                # Parse the response JSON
                transcript_data = response.json()
                # Format it to match YouTubeTranscriptApi format if needed
                return transcript_data
            else:
                st.error(f"Alternative API request failed with status code: {response.status_code}")
                return []
        except Exception as fallback_error:
            st.error(f"Error with alternative transcript API: {str(fallback_error)}")
            return []

def format_time(seconds: float) -> str:
    """Format time in seconds to hh:mm:ss format."""
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def generate_summary(transcript: List[Dict], language: str, summary_type: str) -> str:
    """Generate summary using LLM API based on selected summary type."""
    # transcript_text = "\n".join([f"{format_time(float(entry['start']))}: {entry['text']}" for entry in transcript if isinstance(entry, dict) and 'start' in entry and 'text' in entry])
    # Load JSON data
    transcript = json.dumps(transcript, indent=4)
    transcript = json.loads(transcript)
    transcript = transcript['transcript']

    # Define the format_time function
    def format_time(seconds):
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    # Extract and format transcript
    transcript_text = "\n".join(
        [f"{format_time(float(entry['start']))}: {entry['text']}" for entry in transcript if isinstance(entry, dict) and 'start' in entry and 'text' in entry]
    )

    # print(transcript_text)


    system_prompt = "You are a helpful assistant that creates summaries of YouTube videos from transcripts."
    
    # Adjust the prompt based on summary type
    if summary_type == "detailed":
        user_prompt = f"""
        Please analyze the following YouTube video transcript and create a DETAILED summary.
        Include all important points, key arguments, examples, and data mentioned.
        Structure the summary with clear sections and bullet points where appropriate.
        
        Language for the summary: {language}
        
        Here's the transcript:
        {transcript_text}
        """
    elif summary_type == "brief":
        user_prompt = f"""
        Please analyze the following YouTube video transcript and create a BRIEF summary.
        Focus only on the main ideas and core message of the video - keep it concise.
        Limit to 3-5 key takeaways in a short format.
        
        Language for the summary: {language}
        
        Here's the transcript:
        {transcript_text}
        """
    else:  # normal
        user_prompt = f"""
        Please analyze the following YouTube video transcript and create a balanced summary.
        Capture the main points and key information from the video in a standard length summary.
        
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
    
    cols = st.columns(1)
    cols2 = st.columns(2)
    with cols[0]:
        youtube_url = st.text_input("", placeholder="Paste YouTube URL here...", key="youtube_url", label_visibility="hidden")

    with cols2[0]:
        languages = {
            "en": "🇬🇧 English",
            "zh-TW": "🇹🇼 Traditional Chinese",
            "zh-CN": "🇨🇳 Simplified Chinese",
            "fr": "🇫🇷 French",
            "es": "🇪🇸 Spanish",
            "ja": "🇯🇵 Japanese"
        }
        language = st.selectbox("Summary Language", options=list(languages.keys()), format_func=lambda x: languages[x], label_visibility="hidden")
        st.markdown('</div>', unsafe_allow_html=True)
    with cols2[1]:
        summary_type = {
            "Normal",
            "Brief",
            "Detailed"
        }
        summary_type = st.selectbox("Summary Type", ["Normal", "Brief", "Detailed"], index=0, label_visibility="hidden")
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
                
                transcript = get_youtube_transcript(language, video_id)
                # transcript = json.dumps(transcript, indent=4) # Convert to JSON for debugging   
                # transcript = json.loads(transcript)
                
                
                if transcript:
                    # Update progress
                    status_text.text("Generating summary...")
                    progress_bar.progress(60)
                    
                    # Generate summary
                    summary = generate_summary(transcript, language, summary_type.lower())
                    
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
