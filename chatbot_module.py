from models import db, create_goal #, register_user, complete_goal, update_goal, edit_goal, reset_daily_goals
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os

#############ATTEMPT ONE####################
from langchain import hub
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.schema import StrOutputParser
from langchain_community.chat_message_histories import ChatMessageHistory

from operator import itemgetter

from uuid import uuid4
import os

from langchain_huggingface import HuggingFaceEndpoint
from langchain_core.prompts import PromptTemplate

model_id = "mistralai/Mistral-7B-Instruct-v0.2"
#model_id = "meta-llama/Llama-2-7b-chat"

llm = HuggingFaceEndpoint(
    repo_id=model_id,
    temperature=0.5,
    huggingfacehub_api_token=os.environ["HUGGINGFACEHUB_API_TOKEN"]
)


SESSION_ID = str(uuid4())
print(f"Session ID: {SESSION_ID}")


NAME_PROMPT_TEMPLATE = """You are a user assistant. Helping them decide what they want their next mental or physical health goal to focus on.
Question: {question}
"""

name_prompt = PromptTemplate.from_template(NAME_PROMPT_TEMPLATE)

resources = """
    {
    "SMU resources": [
    {"therapy": "SMU Teletherapy by AcademicLiveCare: High-quality, on-demand mental health care designed specifically for students. All SMU students can now initiate on-demand counseling and video appointments with a medical professional. Find out more [here](https://www.smu.edu/studentaffairs/drbobsmithhealthcenter/counseling-services/mentalhealthapps/smu-teletherapy)."},
    {"recovery": "Collegiate Recovery Community at SMU: Struggling with substance abuse or addiction and need a change? There are students right here on campus going through the same thing who are here to support you. Find out more [here](https://www.smu.edu/studentaffairs/drbobsmithhealthcenter/counseling-services/counselingoptions)."},
    {"wellness": "Campus Well: Check out SMU's health and well-being blog! This site has tons of information written by students for students. Read articles, watch videos, take quizzes and more! Find out more [here](https://smu.campuswell.com/)."},
    {"habits": "WellTrack: Looking for more ways to improve your mental health? Check out WellTrack, SMU's FREE mental health app. The app contains meditation exercises, daily mood checks, stress reduction tips, and much more to help you manage stress, depression, and anxiety while at college. Find out more [here](http://smu.welltrack.com/)."},
    {"mental health" : "TogetherAll: Mental health support. 24/7. Confidential, online peer community. Find out more [here](https://account.v2.togetherall.com/register/student)."}
    ]
}"""


prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful assistant focused solely on helping users set productive MENTAL or PHYSICAL health goals. If the user's question is completely unrelated to health goals, respond with: 'I'm sorry, but I can only assist with questions related to health goals.' Do not infer or generate context-based responses. Keep your responses short and NO REPETITION.",
        ),
        ("system", "{context}"),
        ("placeholder", "{chat_history}"),
        ("human", "Current question: {input}"),

    ]
)

chain = prompt | llm | StrOutputParser()


convo_chain = name_prompt | llm | StrOutputParser()


convo_history = ChatMessageHistory()

chain_with_message_history = RunnableWithMessageHistory(
    chain,
    lambda SESSION_ID: convo_history,
    input_messages_key="input",
    history_messages_key="chat_history"
)

days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


#while True:
def call_chatbot(question, history, user_id):
    q = question

    if q.lower() in ["exit", "quit", "bye", "thank you bye", "goodbye"]:
        prompt_text = "Say goodbye and wish them well."

    # Check for greetings
    is_greeting = any(greet in q.lower() for greet in ["hello", "hi", "hey"])

    is_health_related = any(keyword in q.lower() for keyword in ["health", "goal", "nutrition", "exercise", "mental", "wellness", "meditation", "yoga"])

    is_goal_creation = "create goal" in q.lower() or "set a goal" in q.lower()

    # resource_response = ""
    # if "teletherapy" in q.lower():
    #     resource_response = resources["teletherapy"]
    # elif "recovery" in q.lower():
    #     resource_response = resources["recovery"]
    # elif "wellness" in q.lower():
    #     resource_response = resources["wellness"]
    # elif "mental health" in q.lower():
    #     resource_response = resources["mental health"]
    # elif "mental health management" in q.lower():
    #     resource_response = resources["mental health management"]

    if is_greeting:
        prompt_text = "You are a friendly assistant. When greeted, respond warmly and concisely."
    # elif is_goal_creation:
    #     title = input("What is the title of your goal? ")
    #     category = input("What category is this goal in? ")

        # Display the days of the week for selection
        # reponse = "Which days do you want to work on this goal? (Select by number, separated by commas):" + "\n"
        # for i, day in enumerate(days_of_week):
        #     response += f"{i + 1}. {day}" + "\n"

        # Get user input for days
        # selected_days = input("Enter the numbers of the days (e.g., 1,3,5): ")
        # selected_indices = [int(i.strip()) - 1 for i in selected_days.split(",") if i.strip().isdigit()]
        # days = [i in selected_indices for i in range(len(days_of_week))]

        # reminders = input("Would you like to set reminders? (yes/no) ").lower() == 'yes'
        # weeks = int(input("For how many weeks do you want to set this goal? "))

        # # Create the goal in the database
        # create_goal(db, user_id, title, category, days, reminders, weeks)

        # response = "Your goal has been created successfully! I'm glad I could help and best of luck with your goals :)"
        # updated_history = history + "Human message: " + q + "\n AI Message: " + response + "\n" 
        # return (response, updated_history)

        # prompt_text = "Say goodbye, thank you and wish them well."
    elif is_health_related:
        prompt_text = "You are a helpful assistant focused on health goals. User: {user_input}".format(user_input=q)
    else:
        prompt_text = "Say exactly the following and nothing more: 'I'm sorry, but I can only assist with questions related to health goals.'"



    # Prepare the input data for the model
    input_data = {
        "input": prompt_text,
        "chat_history": history,
        "context" : resources
    }

    # Invoke the chain with the current input and conversation history
    response = chain_with_message_history.invoke(
        input_data,
        config={"configurable": {"session_id": SESSION_ID}}
    )

    return response
    # Print the response
    #print(response)
    #send_response(response)

    # # Add the user and AI messages to the conversation history
    # convo_history.add_message(q)
    # convo_history.add_ai_message(response)

    # # Optional: Clear conversation history after a greeting to limit context
    # if is_greeting:
    #     convo_history.clear()  # or reset to limit context carry-over





# while True:
#     q = input("> ")

#     if q.lower() in ["exit", "quit"]:
#         break

#     # Prepare a context-aware prompt
#     if q.lower() in ["hello", "hi", "hey"]:
#         prompt_text = f"You are a friendly assistant. Respond to greetings warmly and briefly. User: {q}"
#     else:
#         prompt_text = f"You are a helpful assistant. Respond to the following question with relevant information. User: {q}"

#     # Create the input for the model
#     input_data = {
#         "input": prompt_text,
#         "chat_history": convo_history.messages
#     }

#     # Invoke the chain with the current input and conversation history
#     response = chain_with_message_history.invoke(
#         input_data,
#         config={"configurable": {"session_id": SESSION_ID}}
#     )

#     # prompt_text = (
#     #     "You are a friendly assistant. If the user greets you, respond warmly with no additional information and wait for a response from the human. "
#     #     "If they ask a question, provide helpful and relevant information. "
#     #     "User: {user_input}"
#     # ).format(user_input=q)

#     # # Prepare the input data for the model
#     # input_data = {
#     #     "input": prompt_text,
#     #     "chat_history": convo_history.messages
#     # }

#     # # Invoke the chain with the current input and conversation history
#     # response = chain_with_message_history.invoke(
#     #     input_data,
#     #     config={"configurable": {"session_id": SESSION_ID}}
#     # )

#     print(response)

#     # Add the user and AI messages to the conversation history
#     convo_history.add_message(q)
#     convo_history.add_ai_message(response)
