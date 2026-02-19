
import streamlit as st
import sys
import os

# Add 'src' to python path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
# Add project root as well just in case
sys.path.append(os.path.dirname(__file__))

# Import the main app function
from src.app import main

if __name__ == "__main__":
    main()
