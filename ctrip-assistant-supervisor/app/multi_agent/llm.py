from langchain_openai import ChatOpenAI
from config import CONFIG

llm = ChatOpenAI(  # openai的
    temperature=0,
    model=CONFIG['llm']['model_name'],
    api_key=CONFIG['llm']['api_key'],
    base_url=CONFIG['llm']['url'])
