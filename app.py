import streamlit as st
import sys
import os
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import your main app
from ui.app import main

# Vercel configuration
if __name__ == "__main__":
    # Set Streamlit config for Vercel
    port = int(os.environ.get("PORT", 8501))
    address = os.environ.get("STREAMLIT_SERVER_ADDRESS", "0.0.0.0")
    
    # Configure Streamlit
    st.set_page_config(
        page_title="MomFlow AI",
        page_icon="🛍️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Run the main app
    main()
