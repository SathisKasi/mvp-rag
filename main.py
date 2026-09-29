from config import engine,llm
from langchain.tools import tool
from langchain.agents import create_agent

user_question = "What is your name?"

@tool
def company_kb(user_question):
    "need to search the company knowledge base for relevant information"
    print("running company_kb tool")
    return engine.similarity_search(user_question, k=3)

def chatbot(user_question):
    system_prompt = """
    your name is sathis . you are helpful assistant. you are a document assistant. 
    you will answer questions based on the company knowledge base. Use the company_kb tool to find relevant information.

    """
    # result=llm.invoke(system_prompt.format(user_question=user_question, context=context))
    
    agent = create_agent(llm, tools=[company_kb], system_prompt=system_prompt)
    response = agent.invoke({"messages": [{"role": "user", "content": user_question}]})
    return response["messages"][-1].content

answer = chatbot(user_question)
print(answer)