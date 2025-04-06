import streamlit as st
import sys
print("Python executable:", sys.executable)

import assemblyai as aai
import sounddevice as sd
import scipy.io.wavfile as wav
import numpy as np
import time
import os
from datetime import datetime
import requests
import json
import librosa
import pyttsx3
import threading
import logging
logging.basicConfig(level=logging.INFO, filename='app.log',format='%(asctime)s - %(levelname)s - %(message)s')
API_KEY_ASSEMBLY_AI = "API-KEY"

class TextToSpeech:
    def __init__(self):
        self.engine = pyttsx3.init()
        # Configure voice properties
        self.engine.setProperty('rate', 170)    # Speed of speech
        self.engine.setProperty('volume', 0.9)  # Volume (0 to 1)
        
        # Get available voices and set to a professional-sounding voice
        voices = self.engine.getProperty('voices')
        # Try to find a professional-sounding voice
        for voice in voices:
            if "david" in voice.name.lower() or "mark" in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                break
    
    def speak(self, text):
        """Speak text in a non-blocking way"""
        def speak_worker():
            self.engine.say(text)
            self.engine.runAndWait()
        
        # Run speech in a separate thread to not block the UI
        thread = threading.Thread(target=speak_worker)
        thread.start()

class LocalVoiceAgent:
    def __init__(self):
        # Initialize API endpoint for LLM
        self.api_url = "https://rc-156-87.rci.uits.iu.edu/api/chat/completions"
        self.api_key = "API-KEY"
        self.model_name = "Ministral-8B-Instruct-2410-GPTQ"
        
        aai.settings.api_key = API_KEY_ASSEMBLY_AI
        self.transcriber = aai.Transcriber()

        # Initialize text-to-speech
        self.tts = TextToSpeech()
        
        # System prompts
        self.analysis_prompt = [
            {
                "role": "system",
                "content": "You are an interviewer who is an expert at analyzing the response, tone and answer structure of the candidate and giving feedback to improve in under 2000 characters."
            }
        ]
        
        self.full_transcript = self.analysis_prompt.copy()

        self.voice_analysis_prompt = [
            {
                "role": "system",
                "content": f"You are a voice analysis expert. Analyle the audio features extracted from a candidate in an interview and critique it in terms of metrics like nervousness, confidence, tensedness, etc in under 500 characters. **ONLY PRESENT THE SUMMARY, DO NOT DWELL INTO THE TECHNICAL DETAILS**.\nHere are the audio features: "
            }
        ]

    def speak_question(self, question):
        """Speak the interview question"""
        logging.info({"From":["QuestionGenerator"],"Desc": "{question}","To":"QuestionSpeaker"})
        self.tts.speak(question)

    def speak_feedback(self, feedback):
        """Speak the feedback"""
        self.tts.speak(feedback)

    def transcribe_audio_from_file(self, audio_path):
        #print(f"Transcribing: {audio_path}")
        logging.info({"From":["AudioRecorder"],"Desc": "{audio_path}","To":"AudioTranscriber"})
        transcript = self.transcriber.transcribe(audio_path)
        print("Transcript:", transcript.text)
        return transcript.text



    def analyze_response(self, text, question, audio_features):
        """Analyze the interview response using local LLM."""
        try:
            # Prepare messages for content analysis
            messages = self.analysis_prompt.copy()
            messages.append({
                "role": "user",
                "content": f" The question you are critiquing is \" {question}\"\n\nCandidate's Response: {text}"
            })
            self.full_transcript.append({"role": "user", "content": f" The question you are critiquing is \" {question}\"\n\nCandidate's Response: {text}"})

            # Call API for content analysis
            response = self._call_llm_api(messages)
            content_feedback = response
            
            self.full_transcript.append({"role": "assistant", "content": content_feedback})
            
            # Prepare messages for voice analysis
            voice_messages = self.voice_analysis_prompt.copy()
            voice_messages.append({
                "role": "user",
                "content": str(audio_features)
            })
            
            # Call API for voice analysis
            voice_feedback = self._call_llm_api(voice_messages)
            audio_features_str = str(str(audio_features))
            logging.info({"From":["IterativeAnswerCritque","AudioTranscriber","QuestionGenerator","ResumeAnalyzer","Start"],"Desc": "{text}\n{question}","To":"AnswerAnalyzer"})
            logging.info({"From":["AnswerAnalyzer"],"Desc": "{text}\n{question}","To":"IterativeAnswerCritque"})
            logging.info({"From":["AudioToneReader","QuestionGenerator","ResumeAnalyzer","Start"],"Desc": "{audio_features_str}\n{question}","To":"AudioToneAnalyzer"})

            return {
                "content_feedback": content_feedback,
                "voice_feedback": voice_feedback
            }
            
        except Exception as e:
            return f"Error analyzing response: {str(e)}"

    def _call_llm_api(self, messages):
        """Make API call to the local LLM server."""
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": self.model_name,
                "messages": messages
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                return f"API Error: {response.status_code}"
                
        except Exception as e:
            return f"Error calling LLM API: {str(e)}"

def extract_audio_features(audio_file):
    """Extract basic audio features using librosa."""
    try:
        # Load audio file

        y, sr = librosa.load(audio_file, sr=None)
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        energy = np.mean(librosa.feature.rms(y=y))
        pitch = librosa.yin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
        pitch_var = np.var(pitch[~np.isnan(pitch)])
        logging.info({"From":["AudioRecorder"],"Desc": "{audio_file}","To":"AudioToneReader"})
        return {
            "mfcc_mean": np.mean(mfccs, axis=1),
            "chroma_mean": np.mean(chroma, axis=1),
            "energy": energy,
            "pitch_var": float(pitch_var)
        }
    
    except Exception as e:
        print(f"Error extracting audio features: {str(e)}")
        return {"energy": 0.0, "pitch_var": 0.0}

def record_audio(duration=15, fs=16000):
    """Record audio from microphone."""
    try:
        # Create audio directory if it doesn't exist
        os.makedirs("audio_temp", exist_ok=True)
        
        # Generate filename with timestamp
        filename = os.path.join("audio_temp", f"response_{int(time.time())}.wav")
        
        # Record audio
        print(f"Recording for {duration} seconds...")
        audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()
        
        # Save audio file
        wav.write(filename, fs, audio)
        print("Recording saved:", filename)
        logging.info({"From":["Start"],"Desc": "{filename}","To":"AudioRecorder"})
        return filename
    except Exception as e:
        print(f"Error recording audio: {str(e)}")
        return None

def main():
    st.title("Local Interview Practice Assistant")
    
    # Initialize the voice agent
    agent = LocalVoiceAgent()
    questions = [
        {"intro": "Hello! Let's start with a common question.", "question": "Tell me about yourself"},
        {"intro": "Great. Now,", "question": "What are your key strengths?"},
        {"intro": "Interesting. For my next question,", "question": "Why are you interested in this role?"}
    ]
    
    if 'Question' in st.session_state:
        quest = eval(st.session_state['Question'])
        questions = []
        for q in quest:
            questions.append({"intro":"okay","question":q})
    # st.write(questions)
    # Interview questions with introductions
    # Initialize session state
    if 'question_idx' not in st.session_state:
        st.session_state.question_idx = 0
    if 'recording' not in st.session_state:
        st.session_state.recording = False
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False
    if 'question_spoken' not in st.session_state:
        st.session_state.question_spoken = False
    if 'feedback_history' not in st.session_state:
        st.session_state.feedback_history = []
    
    # Display current question
    current_question_data = questions[st.session_state.question_idx]
    st.header(f"Question {st.session_state.question_idx + 1}")
    st.write(current_question_data["question"])

    # Recording controls
    if not st.session_state.recording and not st.session_state.analysis_complete:
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔊 Hear Question"):
                full_question = f"{current_question_data['intro']} {current_question_data['question']}"
                agent.speak_question(full_question)
                st.session_state.question_spoken = True
        
        with col2:
            if st.button("🎤 Start Recording ", disabled=not st.session_state.question_spoken):
                st.session_state.recording = True
                st.rerun()
    
    # Recording in progress
    if st.session_state.recording:
        with st.spinner("Recording your response..."):
            audio_file = record_audio()
            if audio_file:
                # Extract features and analyze
                features = extract_audio_features(audio_file)
                audio_text = agent.transcribe_audio_from_file(audio_file)
                # Analyze response
                feedback = agent.analyze_response(
                    audio_text,  # Currently a placeholder
                    current_question_data["question"],
                    features
                )
                
                # Save feedback to history
                st.session_state.feedback_history.append({
                    "question": current_question_data["question"],
                    "feedback": feedback
                })
                
                # Display feedback
                st.subheader("Interview Feedback")
                
                # Content feedback
                st.markdown("### Content Analysis")
                st.info(feedback["content_feedback"])
                
                # Voice feedback
                st.markdown("### Voice Analysis")
                st.info(feedback["voice_feedback"])
                
                # Clean up
                if os.path.exists(audio_file):
                    os.remove(audio_file)
                
                st.session_state.recording = False
                st.session_state.analysis_complete = True
                st.rerun()
            else:
                st.error("Failed to record audio. Please try again.")
                st.session_state.recording = False
                st.rerun()
    
    # Navigation buttons
    if st.session_state.analysis_complete:
        col1, col2 = st.columns(2)
        
        with col1:
            if st.session_state.question_idx > 0:
                if st.button("⬅️ Previous Question"):
                    st.session_state.question_idx -= 1
                    st.session_state.recording = False
                    st.session_state.analysis_complete = False
                    st.session_state.question_spoken = False
                    st.rerun()
        
        with col2:
            if st.session_state.question_idx < len(questions) - 1:
                if st.button("Next Question ➡️"):
                    st.session_state.question_idx += 1
                    st.session_state.recording = False
                    st.session_state.analysis_complete = False
                    st.session_state.question_spoken = False
                    st.rerun()
            else:
                st.success("🎉 Interview practice complete!")
                
                # Display feedback summary
        if len(st.session_state.feedback_history) > 0:
            st.header("📋 Interview Feedback Summary")
            for idx, feedback_item in enumerate(st.session_state.feedback_history, 1):
                st.subheader(f"Question {idx}: {feedback_item['question']}")
                
                # Content feedback
                st.markdown("**Content Analysis:**")
                st.info(feedback_item['feedback']['content_feedback'])
                
                # Voice feedback
                st.markdown("**Voice Analysis:**")
                st.info(feedback_item['feedback']['voice_feedback'])
                
                if idx < len(st.session_state.feedback_history):
                    st.markdown("---")  # Add separator between questions
    
    # Reset button in sidebar
    with st.sidebar:
        # st.header("Controls")
        # if st.button("Reset Interview"):
        #     st.session_state.question_idx = 0
        #     st.session_state.recording = False
        #     st.session_state.analysis_complete = False
        #     st.session_state.question_spoken = False
        #     st.session_state.feedback_history = []  # Clear feedback history
        #     st.rerun()
        
        # Display tips
        st.markdown("""
        ### Tips
        - Speak clearly and at a normal pace
        - Use a quiet environment
        - Keep your answers focused and concise
        - Take a moment to think before answering
        """)

if __name__ == "__main__":
    main() 