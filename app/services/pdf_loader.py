from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings  # or HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
import os

def load_and_index_pdfs(pdf_folder="knowledge/"):
    docs = []
    if not os.path.exists(pdf_folder):
        return None
    
    for file in os.listdir(pdf_folder):
        if file.endswith(".pdf"):
            loader = PyPDFLoader(os.path.join(pdf_folder, file))
            docs.extend(loader.load())

    if not docs:
        return None

    # 1. Split into chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)

    # 2. Create embeddings
    embeddings = OpenAIEmbeddings()  # requires OPENAI_API_KEY in env

    # 3. Store in FAISS
    vectorstore = FAISS.from_documents(chunks, embeddings)

    # 4. Create retriever
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 4})

    # 5. Build RetrievalQA chain
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True
    )

    return qa_chain
