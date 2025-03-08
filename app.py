import streamlit as st
import re
import json
from typing import Dict, List
from youtube_transcript_api import YouTubeTranscriptApi
from llm import answer_openai, answer
import requests

# External CSS could be moved to a separate file
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
* {font-family: 'Roboto', sans-serif;}
.main {padding: 2rem; max-width: 1200px; margin: 0 auto;}
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
/* Rest of CSS... */
"""

# Set up page configuration
st.set_page_config(
    page_title="YouTube Summary Generator",
    page_icon="📝",
    layout="wide"
)

# Apply custom CSS
st.markdown(f"<style>{CUSTOM_CSS}</style>", unsafe_allow_html=True)

def time_to_seconds(time_str: str) -> float:
    """Convert HH:MM:SS string to seconds (example implementation)."""
    h, m, s = map(int, time_str.split(':'))
    return h * 3600 + m * 60 + s

def format_time(seconds: float) -> str:
    """Format time in seconds to hh:mm:ss format."""
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

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

def get_youtube_transcript(language_code: str, video_id: str) -> Dict:
    """Get the transcript of a YouTube video using primary or fallback API."""
    try:
        # Try to get transcript using the YouTube Transcript API first
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[language_code])
        return {"transcript": transcript}
    except Exception as primary_error:
        try:
            # Fallback to our custom API if YouTube API fails
            fallback_url = f"https://yt.vl.comp.polyu.edu.hk/transcript?password=for_demo&video_id={video_id}"
            response = requests.get(fallback_url)
            
            if response.status_code == 200:
                # Parse the JSON response
                response_data = response.json()
                
                # The API returns a 'transcript' field containing items with 'duration', 'start', and 'text'
                # We'll transform this to include our needed fields
                if "transcript" in response_data:
                    # Process each transcript entry to ensure it has the format we need
                    for entry in response_data["transcript"]:
                        # Ensure we have all required fields
                        if "start" not in entry:
                            entry["start"] = 0.0
                        if "text" not in entry:
                            entry["text"] = ""
                    
                    return response_data
                else:
                    st.error("Transcript data is missing in the API response")
                    return {}
            else:
                st.error(f"Failed to get transcript: API returned status {response.status_code}")
                return {}
        except Exception as fallback_error:
            st.error(f"Failed to get transcript: {str(fallback_error)}")
            return {}


def create_youtube_timestamp_link(video_id: str, timestamp_str: str) -> str:
    """Create a clickable YouTube timestamp link."""
    h, m, s = map(int, timestamp_str.split(':'))
    total_seconds = h * 3600 + m * 60 + s
    return f'[{timestamp_str}](https://www.youtube.com/watch?v={video_id}&t={total_seconds})'

def generate_video_summary(video_id: str, transcript: Dict, language: str, summary_type: str) -> Dict:
    """Generate summary using LLM API based on selected summary type."""
    if not transcript or 'transcript' not in transcript:
        return {"error": "Invalid transcript data"}
    
    transcript_data = transcript['transcript']
    
    # Format transcript for LLM processing
    transcript_text = ""
    transcript_json = []
    
    for idx, entry in enumerate(transcript_data):
        if isinstance(entry, dict) and 'start' in entry and 'text' in entry:
            timestamp = format_time(float(entry['start']))
            text = entry['text']
            transcript_text += f"{timestamp}: {text}\n"
            
            transcript_json.append({
                "id": idx + 1,
                "text": text,
                "start": timestamp
            })
    st.session_state.transcript_text = transcript_text
    # Call LLM API for the actual summary generation
    try:
        llm_response = llm_ask_question(st.session_state.summary_type, st.session_state.transcript_text, respone_format="json_object", language=language)
        
        # print(llm_response)
        # llm_response = {
        #     "sections": [
        #         {
        #             "summary_title": "Section 1: Introduction to RESTful Services",
        #             "start_time": "00:00:00",
        #             "transcript": "(00:00:00) under the hood it needs to talk to a \n(00:00:10) server or the back-end to get or save \n(00:00:15) the data. This communication happens \n(00:00:19) using the HTTP protocol—the same \n(00:00:38) protocol that powers our web. So on the \n(00:00:20) server we expose a bunch of services \n(00:00:22) that are accessible via the HTTP \n(00:00:23) protocol. The client can then directly \n(00:00:24) call the services by sending HTTP \n(00:00:29) requests. Now this is where REST comes into play.",
        #             "summary_content": "An introduction to RESTful services, also known as RESTful APIs, begins by referencing the common client-server architecture. It elaborates on how applications function as clients (the front-end) communicating with servers (the back-end) to retrieve or store data. This communication, conducted using the HTTP protocol, is foundational to web applications and emphasizes the importance of exposing services via HTTP."
        #         },
        #         {
        #             "summary_title": "Section 2: Understanding REST and CRUD Operations",
        #             "start_time": "00:00:27",
        #             "transcript": "(00:00:27) under the hood it needs to talk to a \n(00:00:30) server or the back-end to get or save \n(00:00:33) the data. This communication happens \n(00:00:35) using the HTTP protocol—the same \n(00:00:38) protocol that powers our web. On the \n(00:00:41) server we expose a bunch of services \n(00:00:44) that are accessible via the HTTP \n(00:00:46) protocol. The client can then directly \n(00:00:49) call the services by sending HTTP \n(00:00:52) requests. Now this is where REST comes into focus for operations.",
        #             "summary_content": "REST, which stands for Representational State Transfer, is presented as a design convention for HTTP services. This design supports standard CRUD operations (Create, Read, Update, Delete) on data. A hypothetical example, such as a movie rental service, illustrates how a client app interacts with the server's API—using endpoints like '/api/customers' to manage customer data."
        #         },
        #         {
        #             "summary_title": "Section 3: Implementing RESTful Endpoints",
        #             "start_time": "00:01:00",
        #             "transcript": "(00:01:00) In this section, we dive into how RESTful endpoints are designed and implemented. \nWe discuss how each endpoint corresponds to a particular URI and how HTTP methods like GET, POST, PUT, and DELETE are used to map to CRUD operations. \nDetailed code examples and routing patterns are presented to demonstrate efficient API creation.",
        #             "summary_content": "This section focuses on the practical aspects of building RESTful endpoints. It explains the importance of clear URI design and the proper use of HTTP methods for CRUD operations. Through code samples and routing examples, it provides a roadmap for developers to implement endpoints that are both efficient and maintainable."
        #         },
        #         {
        #             "summary_title": "Section 4: Securing RESTful APIs",
        #             "start_time": "00:02:15",
        #             "transcript": "(00:02:15) Security is a critical component of any API. \nIn this section, we explore how to secure RESTful services by implementing measures like token-based authentication, OAuth protocols, and enforcing HTTPS communication. \nWe also cover common security vulnerabilities and their mitigations.",
        #             "summary_content": "The focus here is on ensuring that RESTful APIs are secure and resilient against threats. It covers key security measures including authentication strategies (like OAuth and token-based systems) and the necessity of using HTTPS. Best practices are discussed to prevent common vulnerabilities and safeguard data integrity."
        #         },
        #         {
        #             "summary_title": "Section 5: Best Practices and Performance Optimization",
        #             "start_time": "00:03:30",
        #             "transcript": "(00:03:30) In the final section, we review best practices to design robust and scalable APIs. \nTopics include the implementation of caching strategies, rate limiting, and load balancing to optimize performance. \nReal-world examples illustrate how these techniques contribute to a high-performance API ecosystem.",
        #             "summary_content": "This concluding section provides guidelines on API design and performance tuning. It discusses best practices such as effective caching, rate limiting, and load balancing. Drawing on practical examples, it offers strategies to ensure that RESTful APIs are efficient, scalable, and capable of handling real-world traffic."
        #         }
        #     ]
        # }
        st.session_state.transcript_list = get_transcript_list(llm_response, transcript)
        
        return llm_response
    except Exception as e:
        return {"error": f"Failed to generate summary: {str(e)}"}

def generate_html_summary(summary_data, video_id):
    """Generate an HTML file from the summary data"""
    try:
        # If summary_data is a string, parse it as JSON
        if isinstance(summary_data, str):
            summary_data = json.loads(summary_data)
        
        # Extract video title from the first section if available
        video_title = "YouTube Summary"
        if "sections" in summary_data and len(summary_data["sections"]) > 0:
            first_section = summary_data["sections"][0]
            if "summary_title" in first_section and first_section["summary_title"].startswith("Section"):
                # Try to extract a more meaningful title
                video_title = first_section["summary_title"].split(":", 1)[1].strip() if ":" in first_section["summary_title"] else first_section["summary_title"]
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{video_title}</title>
            <style>
                body {{
                    font-family: 'Roboto', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                h1 {{
                    color: #FF0000;
                    border-bottom: 2px solid #eee;
                    padding-bottom: 10px;
                }}
                h2 {{
                    color: #333;
                    margin-top: 30px;
                }}
                .timestamp {{
                    color: #0066cc;
                    font-weight: bold;
                }}
                .transcript {{
                    background-color: #f9f9f9;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 10px 0;
                    font-size: 0.9em;
                    white-space: pre-wrap;
                }}
                .summary {{
                    background-color: #f0f8ff;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 15px 0;
                    border-left: 4px solid #0066cc;
                }}
                footer {{
                    margin-top: 50px;
                    text-align: center;
                    font-size: 0.8em;
                    color: #666;
                }}
                a {{
                    color: #0066cc;
                    text-decoration: none;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
            </style>
        </head>
        <body>
            <h1>{video_title}</h1>
            <p>Summary of <a href="https://www.youtube.com/watch?v={video_id}" target="_blank">YouTube video</a></p>
        """
        
        # Add each section
        if "sections" in summary_data:
            for section in summary_data["sections"]:
                title = section.get("summary_title", "Section")
                timestamp = section.get("start_time", "00:00:00")
                transcript = section.get("transcript", "No transcript available")
                summary_content = section.get("summary_content", "No summary available")
                
                youtube_timestamp_url = f"https://www.youtube.com/watch?v={video_id}&t={convert_timestamp_to_seconds(timestamp)}"
                
                html += f"""
                <h2>{title}</h2>
                <p class="timestamp">Timestamp: <a href="{youtube_timestamp_url}" target="_blank">{timestamp}</a></p>
                <div class="transcript">{transcript}</div>
                <div class="summary">{summary_content}</div>
                <hr>
                """
        
        html += """
            <footer>
                Generated with YouTube Summary Generator
            </footer>
        </body>
        </html>
        """
        
        return html
    except Exception as e:
        return f"<html><body><h1>Error generating HTML</h1><p>{str(e)}</p></body></html>"

def convert_timestamp_to_seconds(timestamp):
    """Convert HH:MM:SS timestamp to seconds"""
    h, m, s = map(int, timestamp.split(':'))
    return h * 3600 + m * 60 + s

# Button callback functions
def handle_save_button(section_id):
    return
    # st.session_state.section_states[section_id]["saved"] = not st.session_state.section_states[section_id]["saved"]
    # st.session_state.section_states[section_id]["saved"] = "Saved successfully"

def handle_detail_button(section_id):
    text = llm_ask_question("detailed", not st.session_state.section_states[section_id]["saved"], language=st.session_state.language, respone_format="string")
    parsed_data = json.loads(text)
    text = parsed_data["summary"]
    st.session_state[f"summary_{section_id}"] = text
    # st.session_state.section_states[section_id]["saved"] = text

def handle_concise_button(section_id):
    text = llm_ask_question("more concise", not st.session_state.section_states[section_id]["saved"], language=st.session_state.language, respone_format="string")
    parsed_data = json.loads(text)
    text = parsed_data["summary"]
    st.session_state[f"summary_{section_id}"] = text
    # st.session_state.section_states[section_id]["concise_requested"] = not st.session_state.section_states[section_id]["concise_requested"]

def handle_fun_button(section_id):
    text = llm_ask_question("more fun", not st.session_state.section_states[section_id]["saved"], language=st.session_state.language, respone_format="string")
    parsed_data = json.loads(text)
    text = parsed_data["summary"]
    st.session_state[f"summary_{section_id}"] = text

def handle_generate_summary(youtube_url, language, summary_type):
    if not youtube_url:
        st.warning("Please enter a YouTube URL.")
        return
        
    video_id = extract_video_id(youtube_url)
    
    if not video_id:
        st.error("Invalid YouTube URL. Please check and try again.")
        return
        
    with st.spinner("Getting transcript..."):
        transcript = get_youtube_transcript(language, video_id)
        
    if not transcript:
        st.error("Failed to get transcript. The video might not have subtitles or captions.")
        return
        
    with st.spinner("Generating summary..."):
        summary_data = generate_video_summary(video_id, transcript, language, summary_type)
        st.session_state.summary_data = summary_data

    # if "error" in summary_data:
    #     st.error(f"Error: {summary_data['error']}")
    # else:
    st.success("✅ Summary generated successfully!")
    st.session_state.summary_data = summary_data
    st.session_state.video_id = video_id


def llm_ask_question(summary_type, transcript_text, language, respone_format):
    prompt_prefix = "Based on this YouTube video transcript, "
    
    if summary_type.lower() == "detailed":
        prompt = f"{prompt_prefix}create a DETAILED summary with all key points, organized into 3-5 logical sections."
    elif summary_type.lower() == "brief":
        prompt = f"{prompt_prefix}create a BRIEF summary focusing only on main ideas - keep it concise."
    elif summary_type.lower() == "more concise":
        prompt = f"{prompt_prefix}create an EXTREMELY CONCISE summary with only essential information."
    elif summary_type.lower() == "more fun":
        prompt = f"{prompt_prefix}create an ENTERTAINING summary with humor and engaging language."
    else:  # Normal
        prompt = f"{prompt_prefix}create a balanced summary organized into logical sections."
    
    prompt += f"You must reponse all the content clude the session topic and summary content to the following language: {st.session_state.language}"
    # Store the prompt in session state for debugging
    st.session_state.prompt = prompt

    return answer(system_prompt=prompt, user_prompt=transcript_text, response_format=respone_format, model_type="openrouter")


def get_transcript_list(llm_response, transcript):
    """
    Extract transcript entries that fall within the time ranges of each section in the LLM response.
    
    Args:
        llm_response: Dictionary containing sections with start_time and end_time
        transcript: Dictionary containing transcript entries
        
    Returns:
        List of dictionaries, each containing a section with its matching transcript text
    """
    result = []
    
    # Validate inputs
    if not isinstance(llm_response, dict) or 'sections' not in llm_response:
        return []
    
    if not isinstance(transcript, dict) or 'transcript' not in transcript:
        return []
    
    # Process each section
    for section in llm_response['sections']:
        section_start_time = section.get('start_time', "00:00:00")
        section_end_time = section.get('end_time', "00:00:00")
        section_title = section.get('summary_title', "Untitled Section")
        
        # Convert section times to seconds for comparison
        start_seconds = time_to_seconds(section_start_time)
        end_seconds = time_to_seconds(section_end_time)
        
        # Find transcript entries within this time range
        section_transcript = ""
        for entry in transcript['transcript']:
            entry_start_seconds = entry['start']
            
            # Check if this entry falls within the section timeframe
            if start_seconds <= entry_start_seconds < end_seconds:
                # Format the entry with its timestamp
                entry_time_str = format_time(entry_start_seconds)
                section_transcript += f"({entry_time_str}) {entry['text']}\n"
        
        # If no entries were found, provide a placeholder message
        if not section_transcript:
            section_transcript = f"No transcript entries found for this section ({section_start_time} to {section_end_time})."
        
        # Update the section with the actual transcript text from our data
        section['transcript'] = section_transcript.strip()
        result.append(section)
        print(section)
    # print(result)
    return result


def main():
    # Custom header with animation
    st.markdown('<div class="header-container"><h1 class="app-title">✨ YouTube Summary Generator</h1></div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="animation: fadeIn 1s ease;">
        <p>Get instant summaries of any YouTube video with just one click. 
        Enter a YouTube URL below and select your preferred language.</p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize session state
    if 'summary' not in st.session_state:
        st.session_state.summary = ""
    if 'prompt' not in st.session_state:
        st.session_state.prompt = ""
    if 'llm_output' not in st.session_state:
        st.session_state.llm_output = ""
    if 'section_states' not in st.session_state:
        st.session_state.section_states = {}
    if 'summary_data' not in st.session_state:
        st.session_state.summary_data = {}
    if 'video_id' not in st.session_state:
        st.session_state.video_id = ""

    # Input section
    st.markdown('### 🎬 Enter YouTube Video')
    
    col1 = st.columns(1)[0]
    col2, col3 = st.columns(2)
    
    with col1:
        youtube_url = st.text_input("", placeholder="Paste YouTube URL here...", key="youtube_url", label_visibility="hidden")

    with col2:
        languages = {
            "English": "🇬🇧 English (en)",
            "Traditional Chinese (zh-TW)": "🇹🇼 Traditional Chinese (zh-TW)",
            "Simplified Chinese (zh-CN)": "🇨🇳 Simplified Chinese (zh-CN)",
            "French": "🇫🇷 French",
            "Spanish": "🇪🇸 Spanish",
            "Japanese": "🇯🇵 Japanese"
        }
        language = st.selectbox("Summary Language", options=list(languages.keys()), 
                              format_func=lambda x: languages[x], label_visibility="hidden")
        st.session_state.language = language
    with col3:
        summary_type = st.selectbox("Summary Type", 
                                  ["Normal", "Brief", "Detailed", "More Concise", "More Fun"], 
                                  index=0, label_visibility="hidden")
        st.session_state.summary_type = summary_type

    # Create a dedicated column for the button to control its width and appearance
    btn0_col1, btn0_col2, btn0_col3 = st.columns([1, 2, 1])
    
    # Place the button in the middle column for centered appearance
    with btn0_col2:
        pass  # The actual button is outside this block

    # Generate summary button
    if st.button("✨ Generate Summary"):
        handle_generate_summary(youtube_url, language, summary_type)
            
    # Display summary if available
    if st.session_state.summary_data:
        summary_data = st.session_state.summary_data
        video_id = st.session_state.video_id
    
        # Parse if it's a string
        if isinstance(summary_data, str):
            # try:
            summary_data = json.loads(summary_data)
            # except json.JSONDecodeError:
            #     st.error("Invalid summary data format")
            #     return
        
        # Check if sections exists after parsing
        # if "sections" not in summary_data:
        #     st.error("Summary data does not contain sections")
        #     return
            
        # Add download button for HTML summary
        html_content = generate_html_summary(summary_data, video_id)
        dl_col2 = st.columns([1])  # Fixed the error by providing the spec parameter
        
        with dl_col2[0]:  # Access the first column
            st.download_button(
                label="📥 Download Summary as HTML",
                data=html_content,
                file_name="youtube_summary.html",
                mime="text/html",
                key="download_html"
            )
        
        i = 0
        for section in summary_data['sections']:
            section_id = f"section_{i}"
            if section_id not in st.session_state.section_states:
                st.session_state.section_states[section_id] = {
                    "summary_content": False,
                    "saved": False,
                    "detail_requested": False,
                    "concise_requested": False,
                    "fun_requested": False
                }
            
            timestamp = section['start_time']
            youtube_link = create_youtube_timestamp_link(video_id, timestamp)
            
            # transcript_array = get_transcript_list(llm_response, transcript)
            with st.container():
            # st.subheader(f"Section {i+1}: {section['summary_title']}")
                st.subheader(f"{section['summary_title']}")
                st.markdown(f"Start Time: {youtube_link}", unsafe_allow_html=True)
                st.markdown("<p>Transcript:</p>", unsafe_allow_html=True)
                st.text_area("", section['transcript'], height=100, key=f"transcript_{i}", 
                    disabled=True, label_visibility="collapsed")
            
            
            # Display the summary section label
                st.markdown("Transcript Summary:", unsafe_allow_html=True)

                # st.session_state[f"summary_{i}"] = section["summary_content"]
                st.text_area(
                    "",
                    value=st.session_state.get(f"summary_{section_id}", section.get("summary_content", "No summary available")),
                    height=150,
                    key=f"summary_textarea_{section_id}", 
                    label_visibility="collapsed"
                )
                # Action buttons row - using callbacks for better organization
                btn1, btn2, btn3, btn4 = st.columns(4)
                
                # Get current section state
                section_state = st.session_state.section_states[section_id]
                # print(i)
                with btn1:
                    if st.button("💾 Save", key=f"save_section_{i}", on_click=handle_save_button, args=(section_id,)):
                        pass
                    if section_state["saved"]:
                        pass
                    # st.success("Content saved!")
                
                with btn2:
                    if st.button("🔍 More Detail", key=f"detail_section_{i}", on_click=handle_detail_button, args=(section_id,)):
                        pass
                
                with btn3:
                    if st.button("📝 More Concise", key=f"concise_section_{i}", on_click=handle_concise_button, args=(section_id,)):
                        pass
                    # if section_state["concise_requested"]:
                    #     st.info("Generating more concise content...")
                
                with btn4:
                    if st.button("🎭 More Fun", key=f"fun_section_{i}", on_click=handle_fun_button, args=(section_id,)):
                        pass
                    if section_state["fun_requested"]:
                        st.info("Generating more fun content...")
                
                st.divider()
                i += 1

    # Debug information section
    with st.expander("🔍 Debug Information"):
        tabs = st.tabs(["Prompt", "LLM Output"])
        
        with tabs[0]:
            st.text_area("", value=st.session_state.prompt, height=200, disabled=True, key="prompt_textarea")
            
        with tabs[1]:
            st.text_area("", value=st.session_state.llm_output, height=200, disabled=True, key="llm_output_textarea")

    # Footer
    st.markdown("""
    <div style="text-align: center; margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #eee;">
        <p style="color: #666; font-size: 0.8rem;">Made with ❤️ using Streamlit and AI</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
