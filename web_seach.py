import os
from langchain.agents import initialize_agent, Tool
# from langchain_community.llms import Ollama
from langchain_ollama import OllamaLLM
# from langchain.tools import SerpAPIWrapper
from langchain_community.utilities import SerpAPIWrapper



# --- Setup ---
os.environ["SERPAPI_API_KEY"] = "6e0e22f708cfe9a0ddd065259261d96fb121b677de9224e01e0da76e5c47335f"

# Create search tool
search = SerpAPIWrapper()

# Connect to local Ollama model
llm = OllamaLLM(model="mistral")

# Define the tool
tools = [
    Tool(
        name="Search",
        func=search.run,
        description="Useful for answering questions about current events using web search."
    )
]

# Initialize agent with error handling
agent = initialize_agent(
    tools,
    llm,
    agent="zero-shot-react-description",
    handle_parsing_errors=True,
    verbose=True
)

# Run it
response = agent.invoke({"input": "What's the latest news on OpenAI's GPT models?"})
print(response)
