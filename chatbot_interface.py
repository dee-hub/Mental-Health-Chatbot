# -*- coding: utf-8 -*-
"""Chatbot Interface.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/17DFW7LU_LI27H_ZT43FtvU9h26PVhFjS
"""

import random
import json
import torch
import numpy as np
import nltk
import torch
import torch.nn as nn
import numpy as np
import random
import json
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

nltk.download('wordnet')
nltk.download('omw-1.4')
nltk.download('punkt')

from nltk.stem import WordNetLemmatizer
import openai
import streamlit as st
# pip install streamlit-chat
from streamlit_chat import message
import ibm_db

st.set_page_config(
    page_title="Real-Time Presidential Race Analysis",
    page_icon="logo.png",
    layout="wide",
)

with st.sidebar:
    st.image(image = 'https://assets-cdn.sums.su/HU/images/logos/HUSU_Logo_Master_Blue-250px.webp', use_column_width=True)
    with st.expander("""About HUSU"""):
        st.write(f"""<p style='font-size:13px'>HUSU is a mental health counselling chatbot designed to help you navigate through difficult emotions,
    offer support during challenging times, and provide valuable insights into improving your overall well-being.
    <br>Through its advanced artificial intelligence and empathetic programming, HUSU aims to create a safe and understanding space
    for individuals to express their feelings and thoughts without judgment. Whether you're experiencing stress, anxiety, depression,
    or simply seeking someone to talk to, HUSU is here to listen and offer personalized guidance.
    <br>By utilizing cutting-edge natural language processing, HUSU can comprehend and respond to a wide range of
    emotions and concerns, tailoring its responses to each user's unique needs. </p>""", unsafe_allow_html=True)
styl = f"""
<style>
    .stTextInput {{
      position: fixed;
      bottom: 3rem;
      z-index: 9999;
      border: none;
      border-radius: 4px;
      padding: 10px;
      background-color: #f5f5f5;
      color: #333333;
      font-family: Arial, sans-serif;
      font-size: 14px;
      box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1);
      margin-left: 10px;
      outline: none;
    }}
    .css-1v0mbdj {{
        margin-top: -10px;
    }}
</style>
"""

st.markdown(styl, unsafe_allow_html=True)

#Replace the placeholder values with your actual Db2 hostname, username, and password:
dsn_hostname = "8e359033-a1c9-4643-82ef-8ac06f5107eb.bs2io90l08kqb1od8lcg.databases.appdomain.cloud" # e.g.: "54a2f15b-5c0f-46df-8954-7e38e612c2bd.c1ogj3sd0tgtu0lqde00.databases.appdomain.cloud"
dsn_uid = "klp67023"        # Username
dsn_pwd = "fcD4OYKB3uykMu5F"        # Password

dsn_driver = "{IBM DB2 ODBC DRIVER}"
dsn_database = "BLUDB"            # e.g. "BLUDB"
dsn_port = "30120"                # e.g. "32733" 
dsn_protocol = "TCPIP"            # i.e. "TCPIP"
dsn_security = "SSL"              #i.e. "SSL"

#DO NOT MODIFY THIS CELL. Just RUN it with Shift + Enter
#Create the dsn connection string
dsn = (
    "DRIVER={0};"
    "DATABASE={1};"
    "HOSTNAME={2};"
    "PORT={3};"
    "PROTOCOL={4};"
    "UID={5};"
    "PWD={6};"
    "SECURITY={7};").format(dsn_driver, dsn_database, dsn_hostname, dsn_port, dsn_protocol, dsn_uid, dsn_pwd,dsn_security)

context = [
    {"role": "system", "content": "You are HUSU, a mental health therapist for University of Hull, who\
     uses compassionate listening to have helpful and meaningful conversations with users. HUSU \
     is empathic and friendly. HUSU's objective is to help the user feel better by feeling heard. \
     With each response, HUSU offers follow-up questions to encourage openness and continues \
     the conversation in a natural way., ."},
]
    
if 'context' not in st.session_state:
    st.session_state['context'] = context

openai.api_key = st.secrets['openai']
def continue_conversation(messages, temperature=0.7):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=temperature
    )
    return response.choices[0].message["content"]

def add_prompts_conversation(user_input):
    # Add user input to the conversation
    st.session_state['context'].append({"role": "user", "content": user_input})
    
    # Get response from the model
    response = continue_conversation(st.session_state['context'])
    
    # Add model's response to the conversation
    st.session_state['context'].append({"role": "assistant", "content": response})
    
    # Display the conversation in panels
    return user_input, response


def get_response(msg):
    user, chatbot = add_prompts_conversation(msg)
    conn = ibm_db.connect(dsn, "", "")
    insert_data_sql = "INSERT INTO  KLP67023.CHATBOT_CONVO VALUES (?, ?)"
    prep_stmt = ibm_db.prepare(conn, insert_data_sql)
    ibm_db.bind_param(prep_stmt, 1, user)
    ibm_db.bind_param(prep_stmt, 2, chatbot)
    ibm_db.execute(prep_stmt)
    #print(f"{resp_221} = Uploaded on DB")
    ibm_db.close(conn)

    return chatbot

#Type your questions within the functions

#Creating the chatbot interface
st.title("HUSU: Your Mental Health Counselling Chatbot")

# Storing the chat
if 'generated' not in st.session_state:
    st.session_state['generated'] = []

if 'past' not in st.session_state:
    st.session_state['past'] = []

#def get_text():
 #   input_text = st.text_input("You: ", key="input")
  #  return input_text

def get_text():
    input_text = st.text_input("You: ", key="input", value=st.session_state.get('input_value', ''))
    return input_text

user_input = get_text()
#user_input = st.text_input("You: ", key="input")
if user_input:
    output = get_response(user_input)
    # store the output
    st.session_state.past.append(user_input)
    st.session_state.generated.append(output)
    input_value = '' 
    #st.session_state.input = ''  # Clear the input text
    #st.write('<script>document.getElementById("input").value = "";</script>', unsafe_allow_html=True)
    

if st.session_state['generated']:
    for i in range(len(st.session_state['generated'])-1, -1, -1):
        message(st.session_state["generated"][i], key=str(i))
        message(st.session_state['past'][i], is_user=True, key=str(i) + '_user')
        #st.session_state.past = ''
