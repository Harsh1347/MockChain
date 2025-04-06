import streamlit as st
from resume_analyzer import ResumeAnalyzer
import os
from dotenv import load_dotenv
import time
import streamlit.components.v1 as components
# from local_voice_interview import main_int
import logging
import requests
# Load environment variables
# Configure logging
logging.basicConfig(level=logging.INFO,filename='app.log', format='%(asctime)s - %(levelname)s - %(message)s')
st.session_state['question_to_ask'] = "['Can you please introduce yourself','What Skills align most?']"

load_dotenv()

URL = os.getenv("URL")
API_KEY = os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")
# Initialize API clients
resume_analyzer = ResumeAnalyzer()

def main():
    st.title("MockChain: Interview Preparation Assistant")
    
    # Sidebar for navigation
    # page = st.sidebar.selectbox(
    #     "Choose a feature",
    #     ["Resume Analysis"]
    # )
    
    # if page == "Resume Analysis":
    st.header("Resume Analysis")
    
    # Create two columns for resume upload and job details
    col1, col2 = st.columns(2)
    
    # components.iframe("https://my.spline.design/particles-961fb0c500abd4de81f39bb890c2954c/",width=5000,height=200)

    with col1:
        uploaded_file = st.file_uploader("Upload your resume (PDF or Word)", type=["pdf", "docx"])
    
    with col2:
        company_name = st.text_input("Company Name")
        job_description = st.text_area("Job Description", height=200)
    
    # Add a submit button
    submit_button = st.button("Analyze Resume")
    
    if submit_button:
        if not uploaded_file:
            st.error("Please upload your resume.")
        elif not company_name:
            st.error("Please enter the company name.")
        elif not job_description:
            st.error("Please enter the job description.")
        else:
            logging.info("Identifying Tasks")
            with st.spinner("Analyzing your information..."):
                # st.sidebar.warning("Identifying Task")
                # time.sleep(1)    
                # st.sidebar.warning("Lets Analyse Resume")
                # time.sleep(1)    
                # st.sidebar.warning("Lets Analyse JD")
                # time.sleep(1)    
                # st.sidebar.warning("Running Resume Analyzer Agent")
                # time.sleep(2)
                # st.sidebar.warning("Running JD Analyzer Agent")
                # Extract text directly from the uploaded file
                resume_text = resume_analyzer.extract_text_from_file(uploaded_file)

                if isinstance(resume_text, str) and not resume_text.startswith("Error"):
                    # Create tabs for different analyses
                    tab1, tab2, tab3 = st.tabs([
                        # "Resume Analysis",
                        "Skill Gap Analysis",
                        "Interview Preparation",
                        "Sample Question"
                        # "Mock Interview"
                    ])
                    
                    # with tab1:
                    # st.write("### Resume Analysis")
                    analysis = resume_analyzer.analyze_resume(resume_text)
                    # print(analysis)
                    # st.write(analysis)
                    logging.info({"From":["IterativeAnswerCritque","AudioTranscriber","ResumeAnalyzer","SkillGapAnalyzer","CompanyResearcher","LeetcodeResearcher"],"Desc": "{resume_text}\n{analysis}","To":"QuestionGenerator"})

                    QUESTION_GENERATOR_PROMPT = f"""
                    You are a Question Generator Agent.
                    Using the outputs from the JD Analyzer and Resume Matcher agents {analysis}, generate:
                    - 1 phone screening question. This should start by asking an introduction
                    - 1 job-fit question,
                    - 1 resume-based question,

                    Return a **python list** of questions. **NOTHING ELSE**. **NO FORMATTING REQUIRED**
                    
                            """
                            
                    headers = {
                                    "Content-Type": "application/json",
                                    "Authorization": f"Bearer {API_KEY}"
                                }
                                
                    payload = {
                                    "model": MODEL_NAME,
                                    "messages": [{"role": "user","content":QUESTION_GENERATOR_PROMPT}]
                    }
                    response = requests.post(
                                    URL,
                                    headers=headers,
                                    json=payload
                                )
                    if response.status_code == 200:
                        def extract_bracket_content(text):
                            start = text.find('[')
                            end = text.rfind(']')
                            if start != -1 and end != -1 and start < end:
                                return text[start:end+1]
                            return''
                    questions_to_ask = extract_bracket_content(response.json()["choices"][0]["message"]["content"])
                        
                    
                    st.session_state['question_to_ask'] = questions_to_ask
                    
                    # st.write("### Initial Career Assessment")
                    career_assessment = resume_analyzer.get_career_path_advice(resume_text, job_description)
                    # st.write(career_assessment)
                    
                    with tab1:
                        st.write("### Skill Gap Analysis")
                        gap_analysis = resume_analyzer.get_skill_gap_analysis(resume_text, job_description)
                        st.write(gap_analysis)
                    
                    with tab2:
                        st.write("### Interview Preparation")
                        # Generate company insights using LLM
                        company_insights = resume_analyzer.get_company_insights(company_name)
                        st.write("#### Company Interview Process & Culture")
                        st.write(company_insights)
                        
                        # Generate interview prep content
                        prep_content = resume_analyzer.generate_interview_prep(
                            resume_text,
                            job_description,
                            company_name
                        )
                        st.write("#### Interview Preparation Guide")
                        st.write(prep_content)
                        
                        # Generate LeetCode recommendations
                        leetcode_prep = resume_analyzer.get_leetcode_recommendations(job_description)
                        st.write("#### Recommended LeetCode Preparation")
                        st.write(leetcode_prep)

                    with tab3:
                        st.write("### Questions on resume")
                        # career_path = resume_analyzer.get_career_path_advice(resume_text, job_description)
                        st.session_state['Question'] = questions_to_ask
                        #st.write(eval(questions_to_ask))
                        for q in eval(questions_to_ask):
                            st.write(q)
    
  

if __name__ == "__main__":
    main() 