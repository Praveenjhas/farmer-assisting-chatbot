# -*- coding: utf-8 -*-
"""biomedical.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1eAt0fEFY_DOFx9e161hYpRCuJga6OSYg
"""

from google.colab import drive
drive.mount('/content/drive')
!pip install langchain sentence-transformers chromadb llama-cpp-python langchain_community pypdf
!pip install -q -U langchain transformers bitsandbytes accelerate
import torch
from langchain import PromptTemplate, HuggingFacePipeline
from transformers import BitsAndBytesConfig, AutoModelForCausalLM, AutoTokenizer, GenerationConfig, pipeline
import os

# Set Hugging Face Token
os.environ["HF_TOKEN"] = "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"

# Define model
MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.2"

# Initialize tokenizer
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=True)
tokenizer.pad_token = tokenizer.eos_token

# Configure quantization
quantization_config = BitsAndBytesConfig(load_in_4bit=True)

# Initialize language model
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float16,
    trust_remote_code=True,
    device_map="auto",
    quantization_config=quantization_config
)

# Set generation configuration
generation_config = GenerationConfig.from_pretrained(MODEL_NAME)
generation_config.max_new_tokens = 1024
generation_config.temperature = 0.7
generation_config.top_p = 0
generation_config.do_sample = True

# Assign generation config to model
model.config.generation_config = generation_config

# Create pipeline
pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    return_full_text=True,
    generation_config=generation_config
)

# Initialize LangChain LLM
llm = HuggingFacePipeline(pipeline=pipe)

#importing libraries
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain.vectorstores import Chroma
from langchain_community.llms import LlamaCpp

from langchain.chains import RetrievalQA,LLMMathChain

"""Import the document

"""

loader=PyPDFDirectoryLoader("/content/drive/MyDrive/Stawberry and Lettuce")
docs=loader.load()

len(docs) ##no of pages
docs[400]

"""Chunking"""

text_splitter=RecursiveCharacterTextSplitter(chunk_size=300,chunk_overlap=50)
chunks=text_splitter.split_documents(docs)
len(chunks)

chunks[501]

"""Embeddings creations

using llamaindex
"""

embeddings=SentenceTransformerEmbeddings(model_name="NeuML/pubmedbert-base-embeddings")

"""Vector Store creation

"""

vectorstore=Chroma.from_documents(chunks,embeddings)

query="tell me how to cure the diesese in my streaberry plant?"
search_results=vectorstore.similarity_search(query)
search_results

retriever=vectorstore.as_retriever(search_kwargs={"k":5})
retriever.get_relevant_documents(query) # Changed 'get_relevent_documents' to 'get_relevant_documents'

"""use llm and retriver and query,to generate final response


"""

template="""
<|context|>
you are the helper to help the farmers to solve their qureries related to their plants
please answer the question in the appropraite manner
</s>
<|user|>
{query}
</s>
<|assistant|>
"""

from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from langchain.prompts import ChatPromptTemplate

prompt=ChatPromptTemplate.from_template(template)

rag_chain=(
    {"context": retriever,"query":RunnablePassthrough()}
    |prompt
    |llm
    |StrOutputParser()
)

response=rag_chain.invoke(query)

response

newquery="it is some bacterial leaf spot as i can see"
rag_chain.invoke(newquery)

import sys
while True:
  user_input=input(f"Input query: ")
  if user_input=="exit":
     print("Exiting...")
     sys.exit()
  if user_input=="":
   continue
  result=rag_chain.invoke(user_input)
  print(result)
