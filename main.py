import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from src.system_initializer import SystemInitializer
from src.video_processor import VideoProcessor
from src.utilities import Utilities
import asyncio
import warnings
warnings.filterwarnings("ignore")  # Ignore warnings for a cleaner output

class OCRChatbotApp:
    def __init__(self):
        # Initialize the system components
        self.system_initializer = SystemInitializer()
        self.utilities = Utilities()
        self.queues = self.system_initializer.initialize_system()  # Initialize queues and start OCR thread
        self.conf_thresh = 50  # Default confidence threshold for OCR
        self.n = 5  # Process every n frames
        self.k = 30  # Number of frames to keep annotations

    async def run_chatbot_async(self):
        """Run the chatbot asynchronously to keep the app responsive."""
        await self.system_initializer.run_chatbot_async()

    def run(self):
        st.title('OCR and Chatbot Application')  # Set the title of the Streamlit app

        # Initialize session state variables if they don't exist
        if "camera_frozen" not in st.session_state:
            st.session_state.update({"camera_frozen": False, "latest": [], "likely_text": ""})

        # Create sliders for adjusting confidence threshold and frame processing interval
        self.conf_thresh = st.slider('Confidence Threshold', 0, 100, 50)
        self.n = st.slider('Process every n frames', 1, 30, 5)

        # Button to freeze or resume the camera
        if st.button("Freeze" if not st.session_state.camera_frozen else "Resume", key="freeze_resume"):
            st.session_state.camera_frozen = not st.session_state.camera_frozen
            if st.session_state.camera_frozen:
                # Fetch likely text asynchronously to avoid freezing the UI
                with st.spinner("Processing..."):
                    st.session_state.likely_text = self.utilities.fetch_likely_text()

        # Define constraints for higher resolution video capture
        constraints = {
            "video": {
                "width": {"ideal": 1280},
                "height": {"ideal": 720},
                "frameRate": {"ideal": 30}
            },
            "audio": False
        }

        # Initialize the WebRTC streamer with optimized settings
        webrtc_ctx = webrtc_streamer(
            key="example",
            mode=WebRtcMode.SENDRECV,
            video_processor_factory=lambda: VideoProcessor(self.queues, self.conf_thresh, self.n, self.k),
            media_stream_constraints=constraints,
            async_processing=True,
        )

        # Display the likely text if the camera is frozen
        if st.session_state.camera_frozen and st.session_state.likely_text:
            st.write(f"Detected Text: {st.session_state.likely_text}")
        else:
            st.write("No text detected yet. Make sure the camera is running.")

        # Run the chatbot asynchronously for smoother performance
        asyncio.run(self.run_chatbot_async())


if __name__ == '__main__':
    app = OCRChatbotApp()  # Create an instance of the OCRChatbotApp
    app.run()  # Run the app
