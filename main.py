import os
import sys
import streamlit as st
#from dotenv import load_dotenv
from pathlib import Path

# Add the app-tester directory to Python path
app_tester_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(app_tester_dir))

# Import from the same directory
try:
    from redflag_agent import classify_prompt
except ImportError:
    # Fallback: try importing with full path
    import importlib.util
    spec = importlib.util.spec_from_file_location("redflag_agent", app_tester_dir / "redflag_agent.py")
    redflag_agent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(redflag_agent)
    classify_prompt = redflag_agent.classify_prompt

# Load .env file from project root (optional fallback)
project_root = Path(__file__).resolve().parent.parent
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)

st.set_page_config(
    page_title="AI Red-Flag Detector (Tester Version)",
    page_icon="🚩",
    layout="centered",
    initial_sidebar_state="expanded",  # Make sure sidebar is visible
)

st.title("🚩 Trust & Safety bot - dating app(Tester Version)")
st.write(
    "Classify dating-profile text as SAFE, MANIPULATIVE, UNSAFE, or OBJECTIFYING and get a short explanation."
)

# API Key Input Section - Make it prominent in the main area first
st.info("🔑 **API Key Required:** Please enter your OpenAI API key in the sidebar (left side) to use this application.")

with st.expander("Policy & Limitations"):
    st.markdown(
        "- This is a micro-policy demo for Trust & Safety prototyping.\n"
        "- It may produce false positives/negatives; human review is required.\n"
        "- Categories: SAFE, MANIPULATIVE, UNSAFE, OBJECTIFYING.\n"
        "- **You need to provide your own OpenAI API key to use this application.**\n"
        "- Your API key is only used for this session and is not stored."
    )

# API Key Input Section in Sidebar
st.sidebar.header("🔑 API Configuration")
st.sidebar.markdown("**Required:** Enter your OpenAI API key below")

# Check if API key is in session state
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# Get API key from user
api_key_input = st.sidebar.text_input(
    "OpenAI API Key",
    value=st.session_state.api_key,
    type="password",
    help="Enter your OpenAI API key. Get one at https://platform.openai.com/api-keys",
    placeholder="sk-..."
)

# Update session state
if api_key_input:
    st.session_state.api_key = api_key_input

# Model selection
model_options = {
    "gpt-4o-mini (Recommended - Fast & Cost-effective)": "gpt-4o-mini",
    "gpt-4o": "gpt-4o",
    "gpt-4-turbo": "gpt-4-turbo",
    "gpt-3.5-turbo": "gpt-3.5-turbo",
}

selected_model = st.sidebar.selectbox(
    "OpenAI Model",
    options=list(model_options.keys()),
    index=0,
    help="Choose which OpenAI model to use for classification"
)

model_name = model_options[selected_model]

# Show API key status
if st.session_state.api_key:
    st.sidebar.success("✅ API Key provided")
    # Show first and last 4 characters for verification
    masked_key = f"{st.session_state.api_key[:7]}...{st.session_state.api_key[-4:]}" if len(st.session_state.api_key) > 11 else "***"
    st.sidebar.caption(f"Key: {masked_key}")
else:
    st.sidebar.warning("⚠️ API Key required")

# Main input area
st.header("Enter Text to Classify")
text = st.text_area(
    "Profile text", 
    height=160, 
    placeholder="e.g., Only swipe if you're fit and rich.",
    label_visibility="collapsed"
)

if st.button("Analyze", type="primary", use_container_width=True):
    # Validate API key
    if not st.session_state.api_key or not st.session_state.api_key.strip():
        st.error("❌ Please enter your OpenAI API key in the sidebar to continue.")
        st.info("💡 Get your API key at: https://platform.openai.com/api-keys")
    elif not text.strip():
        st.error("Please enter some text to analyze.")
    else:
        # Validate API key format (should start with sk-)
        if not st.session_state.api_key.startswith("sk-"):
            st.warning("⚠️ API key format looks incorrect. OpenAI keys usually start with 'sk-'")
        
        with st.spinner(f"Analyzing with {model_name}..."):
            try:
                result = classify_prompt(
                    text, 
                    api_key=st.session_state.api_key,
                    model=model_name
                )
                
                #st.subheader("Result")
                #st.json(result, expanded=True)
                
                # Show category with color coding
                category = result.get("category", "SAFE")
                explanation = result.get("explanation", "")
                
                # Color coding for categories
                category_colors = {
                    "SAFE": "🟢",
                    "MANIPULATIVE": "🟡",
                    "UNSAFE": "🔴",
                    "OBJECTIFYING": "🟠",
                }
                
                emoji = category_colors.get(category, "⚪")
                st.markdown(f"### {emoji} Category: **{category}**")
                st.markdown(f"**Explanation:** {explanation}")
                
            except ValueError as e:
                st.error(f"❌ API Key Error: {e}")
                st.info("Please check your API key and try again.")
            except Exception as e:
                st.error(f"❌ Error: {e}")
                st.info("Please check your API key and try again. Make sure you have credits in your OpenAI account.")

# Footer
st.markdown("---")
st.caption("💡 **Note:** Your API key is stored only in your browser session and is never saved or transmitted to any server except OpenAI's API.")


