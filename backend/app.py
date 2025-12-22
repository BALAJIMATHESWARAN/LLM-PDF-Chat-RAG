from flask import Flask, request, jsonify
from flask_cors import CORS
from PyPDF2 import PdfReader
from docx import Document
from PIL import Image
import pytesseract
import pandas as pd
import os

from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI

# ---------------- INIT ----------------
load_dotenv()
app = Flask(__name__)
CORS(app)

# ---------------- EMBEDDINGS ----------------
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)


db = None  # global vector store

# ---------------- FILE TEXT EXTRACTION ----------------
def extract_text(file):
    name = file.filename.lower()

    if name.endswith(".pdf"):
        reader = PdfReader(file)
        return "".join(page.extract_text() or "" for page in reader.pages)

    elif name.endswith(".docx"):
        doc = Document(file)
        return "\n".join(p.text for p in doc.paragraphs)

    elif name.endswith(".txt"):
        return file.read().decode("utf-8")

    elif name.endswith(".csv"):
        df = pd.read_csv(file)
        return df.to_string()

    elif name.endswith((".png", ".jpg", ".jpeg")):
        img = Image.open(file)
        return pytesseract.image_to_string(img)

    return ""

# ---------------- UPLOAD ROUTE ----------------
@app.route("/upload", methods=["POST"])
def upload():
    global db
    print("📥 Upload request received")

    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "No files uploaded"}), 400

    combined_text = ""
    for file in files:
        combined_text += extract_text(file) + "\n"

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = splitter.split_text(combined_text)

    db = FAISS.from_texts(chunks, embeddings)

    print("✅ Files processed successfully")
    return jsonify({"message": f"{len(files)} files uploaded successfully"})

# ---------------- ASK ROUTE ----------------
@app.route("/ask", methods=["POST"])
def ask():
    global db
    print("❓ Question request received")

    if db is None:
        return jsonify({"answer": "Please upload files first"}), 400

    data = request.get_json()
    question = data.get("question")

    llm = ChatOpenAI(
        model="meta-llama/llama-3.1-8b-instruct",
        temperature=0,
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1"
    )

    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=db.as_retriever()
    )

    answer = qa.invoke({"query": question})["result"]
    print("✅ Answer generated")

    return jsonify({"answer": answer})

# ---------------- RUN SERVER ----------------
if __name__ == "__main__":
    app.run(port=5000, debug=False, use_reloader=False)
