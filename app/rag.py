import os
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings

KNOWLEDGE_DIR = os.path.join("chatbot", "knowledge")
INDEX_PATH = os.path.join(KNOWLEDGE_DIR, "faiss_index")

def load_pdfs(pdf_folder=KNOWLEDGE_DIR):
    docs = []
    if not os.path.exists(pdf_folder):
        return docs

    for file in os.listdir(pdf_folder):
        if file.endswith(".pdf"):
            loader = PyPDFLoader(os.path.join(pdf_folder, file))
            docs.extend(loader.load())

    return docs

def build_vector_store():
    docs = load_pdfs()
    if not docs:
        return None

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)

    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(INDEX_PATH)

    return vectorstore

def get_vector_store():
    if os.path.exists(INDEX_PATH):
        return FAISS.load_local(INDEX_PATH, OpenAIEmbeddings())
    return build_vector_store()
