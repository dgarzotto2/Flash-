import streamlit as st
import requests
from PIL import Image
import io

# Function to download and display images using Pillow (PIL)
def show_image(image_url):
    try:
        # Attempt to download the image from the URL
        response = requests.get(image_url)
        response.raise_for_status()  # Check for request errors
        
        # Open the image using Pillow
        img = Image.open(io.BytesIO(response.content))
        
        # Display the image in Streamlit
        st.image(img, caption="Image from URL", use_column_width=True)
    except Exception as e:
        st.error(f"❌ Failed to load image: {e}")

# Main function to handle the app logic
def main():
    st.title("Simplified Streamlit App (No imghdr)")

    # Input for URL of an image
    image_url = st.text_input("Enter Image URL to display:")

    if image_url:
        # If URL is provided, display the image
        show_image(image_url)

    # Additional message to show in the app
    st.write("This is a simplified Streamlit app using Pillow to handle images.")
    
    # Optional: Include any other features or buttons for the app if needed
    st.write("You can add more functionalities here!")

# Ensure the main function runs when the script is executed
if __name__ == "__main__":
    main()
