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

lemmatizer = WordNetLemmatizer()

def tokenize(sentence):
    """
    split sentence into array of words/tokens
    a token can be a word or punctuation character, or number
    """
    return nltk.word_tokenize(sentence)


def lemma(word):
    """
    stemming = find the root form of the word
    examples:
    words = ["organize", "organizes", "organizing"]
    words = [stem(w) for w in words]
    -> ["organ", "organ", "organ"]
    """
    return lemmatizer.lemmatize(word.lower(), pos='v')


def bag_of_words(tokenized_sentence, words):
    """
    return bag of words array:
    1 for each known word that exists in the sentence, 0 otherwise
    example:
    sentence = ["hello", "how", "are", "you"]
    words = ["hi", "hello", "I", "you", "bye", "thank", "cool"]
    bog   = [  0 ,    1 ,    0 ,   1 ,    0 ,    0 ,      0]
    """
    # stem each word
    sentence_words = [lemma(word) for word in tokenized_sentence]
    # initialize bag with 0 for each word
    bag = np.zeros(len(words), dtype=np.float32)
    for idx, w in enumerate(words):
        if w in sentence_words:
            bag[idx] = 1

    return bag

class NeuralNet(nn.Module):
    def __init__(self, input_size, hidden_size, num_classes):
        super(NeuralNet, self).__init__()
        self.l1 = nn.Linear(input_size, hidden_size)
        self.l2 = nn.Linear(hidden_size, hidden_size)
        self.l3 = nn.Linear(hidden_size, num_classes)
        self.relu = nn.ReLU()

    def forward(self, x):
        out = self.l1(x)
        out = self.relu(out)
        out = self.l2(out)
        out = self.relu(out)
        out = self.l3(out)
        # no activation and no softmax at the end
        return out

with open('intents.json', 'r') as f:
    intents = json.load(f)

all_words = []
tags = []
xy = []

for intent in intents['intents']:
    tag = intent['tag']
    # add to tag list
    tags.append(tag)
    for pattern in intent['patterns']:
        # tokenize each word in the sentence
        w = tokenize(pattern)
        # add to our words list
        all_words.extend(w)
        # add to xy pair
        xy.append((w, tag))

# stem and lower each word
ignore_words = ['?', '.', '!']
all_words = [lemma(w) for w in all_words if w not in ignore_words]
# remove duplicates and sort
all_words = sorted(set(all_words))
tags = sorted(set(tags))

print(len(xy), "patterns")
print(len(tags), "tags:", tags)
print(len(all_words), "unique lemmatized words:", all_words)

# create training data
X_train = []
y_train = []
for (pattern_sentence, tag) in xy:
    # X: bag of words for each pattern_sentence
    bag = bag_of_words(pattern_sentence, all_words)
    X_train.append(bag)
    # y: PyTorch CrossEntropyLoss needs only class labels, not one-hot
    label = tags.index(tag)
    y_train.append(label)

X_train = np.array(X_train)
y_train = np.array(y_train)

# Hyper-parameters
num_epochs = 1000
batch_size = 8
learning_rate = 0.001
input_size = len(X_train[0])
hidden_size = 8
output_size = len(tags)
print(input_size, output_size)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

with open('intents.json', 'r') as json_data:
    intents = json.load(json_data)

FILE = "bot.pth"
data = torch.load(FILE)

input_size = data["input_size"]
hidden_size = data["hidden_size"]
output_size = data["output_size"]
all_words = data['all_words']
tags = data['tags']
model_state = data["model_state"]

model = NeuralNet(input_size, hidden_size, output_size).to(device)
model.load_state_dict(model_state)
model.eval()

bot_name = "Aura"

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

def get_response(msg):
    sentence = tokenize(msg)
    
    X = bag_of_words(sentence, all_words)
    X = X.reshape(1, X.shape[0])
    X = torch.from_numpy(X).to(device)

    output = model(X)
    _, predicted = torch.max(output, dim=1)

    tag = tags[predicted.item()]

    probs = torch.softmax(output, dim=1)
    prob = probs[0][predicted.item()]
    if prob.item() > 0.85:
        for intent in intents['intents']:
            if tag == intent["tag"]:
                print(f"Identified context = {tag}")
                conn = ibm_db.connect(dsn, "", "")
                insert_data_sql = """
                INSERT INTO CHATBOT_CONVO (chatbot_responses)
                VALUES (random.choice(intent['responses']))
                """
                # Execute the SQL statement to insert data
                #conn = ibm_db.connect(dsn, "", "")
                stmt = ibm_db.exec_immediate(conn, insert_data_sql)
                print(f"{random.choice(intent['responses'])} = Uploaded on DB")
                ibm_db.close(conn)
                return random.choice(intent['responses'])
                
    else:
        conn = ibm_db.connect(dsn, "", "")
        insert_data_sql = """
        INSERT INTO CHATBOT_CONVO (chatbot_responses)
        VALUES ("I do not understand")
        """
        # Execute the SQL statement to insert data
        #conn = ibm_db.connect(dsn, "", "")
        stmt = ibm_db.exec_immediate(conn, insert_data_sql)
        print(f"I do not understand = Uploaded on DB")
        ibm_db.close(conn)
        
        return "I do not understand..."

#Type your questions within the functions

#Creating the chatbot interface
st.title("Aura: Your Mental Health Counselling Chatbot")

# Storing the chat
if 'generated' not in st.session_state:
    st.session_state['generated'] = []

if 'past' not in st.session_state:
    st.session_state['past'] = []

def get_text():
    input_text = st.text_input("You: ", key="input")
    return input_text

user_input = get_text()
conn = ibm_db.connect(dsn, "", "")
insert_data_sql = "INSERT INTO  KLP67023.CHATBOT_CONVO (user_conversations) VALUES (?,)"

prep_stmt = ibm_db.prepare(conn, insert_data_sql)
ibm_db.bind_param(prep_stmt, 1, user_input)
ibm_db.execute(prep_stmt)

#insert_data_sql = """
#INSERT INTO CHATBOT_CONVO (user_chats)
#VALUES ("{quoted_user_input}") 
#"""
# Execute the SQL statement to insert data
#stmt = ibm_db.exec_immediate(conn, insert_data_sql)
print(f"{user_input} = Uploaded on DB")
ibm_db.close(conn)

if user_input:
    output = get_response(user_input)
    # store the output
    st.session_state.past.append(user_input)
    st.session_state.generated.append(output)
    

if st.session_state['generated']:
    for i in range(len(st.session_state['generated'])-1, -1, -1):
        message(st.session_state["generated"][i], key=str(i))
        message(st.session_state['past'][i], is_user=True, key=str(i) + '_user')
        #st.session_state.past = ''
