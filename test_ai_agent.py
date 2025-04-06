from ollama import Client

# Connect to the local Ollama server
client = Client(host='http://localhost:11434')  # default port

def extract_job_details_ollama(job_description):
    prompt = f"""
You are a helpful assistant that extracts structured information from job descriptions.

Given this job description, extract:
- Job Title
- Company Name (if available)
- Location
- Responsibilities (as a list)
- Required Skills (as a list)
- Preferred Qualifications (as a list)

Return the result in clean JSON format.

Job Description:
\"\"\"
{job_description}
\"\"\"
"""

    response = client.chat(model='mistral', messages=[
        {"role": "user", "content": prompt}
    ])

    return response['message']['content']

# Example usage
if __name__ == "__main__":
    jd = """
We are hiring a Machine Learning Intern at Pinterest for Summer 2025. The role is based in San Francisco, CA.

Responsibilities:
- Analyze large-scale data to understand user behavior
- Build models for recommendation systems

Requirements:
- Python
- Experience with ML libraries like Scikit-learn or TensorFlow
- SQL
Preferred:
- Familiarity with deep learning
- Previous internship experience in tech
"""

    result = extract_job_details_ollama(jd)
    print(result)
