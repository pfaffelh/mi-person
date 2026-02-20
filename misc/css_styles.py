import streamlit as st

# css-style for right allignment
def init_css():
    st.markdown("""
        <style>
        .element-container:has(style){
            display: none;
        }
        #align-right {
            display: none;
        }
        .element-container:has(#align-right) {
            display: none;
        }
        .element-container:has(#align-right) + div button {
            float: right;
            }
        </style>
        """,
        unsafe_allow_html=True,)

    # Change color of multiselect choise-boxes
    st.markdown(
        """
    <style>
    span[data-baseweb="tag"] {
      background-color: orange !important;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )
