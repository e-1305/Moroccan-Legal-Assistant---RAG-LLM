import os
from pathlib import Path
from time import time

import dotenv
import streamlit as st
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    Docx2txtLoader,
    PyPDFLoader,
    WebBaseLoader,
)
from langchain_community.document_loaders.text import TextLoader
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_openai import AzureOpenAIEmbeddings, OpenAIEmbeddings

dotenv.load_dotenv()

os.environ.setdefault("USER_AGENT", "moroccan-legal-assistant")

DB_DOCS_LIMIT = 10
MAX_COLLECTIONS_IN_MEMORY = 20

# Legal texts are made of short articles: small chunks keep each retrieved
# passage close to a single article, which makes citations meaningful.
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200

CORPUS_DIR = Path(__file__).parent / "corpus"


def stream_llm_response(llm_stream, messages):
    """Plain LLM answer, without retrieval."""
    response_message = ""

    for chunk in llm_stream.stream(messages):
        response_message += chunk.content
        yield chunk

    st.session_state.messages.append({"role": "assistant", "content": response_message})


# --- Indexing Phase ---

def _loader_for(file_path, file_name, mime_type=None):
    if file_name.endswith(".pdf") or mime_type == "application/pdf":
        return PyPDFLoader(file_path)
    if file_name.endswith(".docx"):
        return Docx2txtLoader(file_path)
    if file_name.endswith((".txt", ".md")) or mime_type in ("text/plain", "text/markdown"):
        return TextLoader(file_path)
    return None


def load_doc_to_db():
    """Index the files uploaded through the sidebar."""
    if not st.session_state.get("rag_docs"):
        return

    docs = []
    loaded_names = []
    for doc_file in st.session_state.rag_docs:
        if doc_file.name in st.session_state.rag_sources:
            continue
        if len(st.session_state.rag_sources) >= DB_DOCS_LIMIT:
            st.error(f"Maximum number of documents reached ({DB_DOCS_LIMIT}).")
            break

        os.makedirs("source_files", exist_ok=True)
        file_path = f"./source_files/{doc_file.name}"
        with open(file_path, "wb") as file:
            file.write(doc_file.read())

        try:
            loader = _loader_for(file_path, doc_file.name, doc_file.type)
            if loader is None:
                st.warning(f"Document type {doc_file.type} not supported.")
                continue

            loaded = loader.load()
            for d in loaded:
                d.metadata["source"] = doc_file.name
            docs.extend(loaded)
            st.session_state.rag_sources.append(doc_file.name)
            loaded_names.append(doc_file.name)

        except Exception as e:
            st.toast(f"Error loading document {doc_file.name}: {e}", icon="⚠️")
            print(f"Error loading document {doc_file.name}: {e}")

        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

    if docs:
        _split_and_load_docs(docs)
        st.toast(f"Loaded: {', '.join(loaded_names)}", icon="✅")


def load_url_to_db():
    """Index the content of a web page entered in the sidebar."""
    url = st.session_state.get("rag_url")
    if not url or url in st.session_state.rag_sources:
        return
    if len(st.session_state.rag_sources) >= DB_DOCS_LIMIT:
        st.error(f"Maximum number of documents reached ({DB_DOCS_LIMIT}).")
        return

    try:
        docs = WebBaseLoader(url).load()
    except Exception as e:
        st.error(f"Error loading document from {url}: {e}")
        return

    if docs:
        st.session_state.rag_sources.append(url)
        _split_and_load_docs(docs)
        st.toast(f"Document from URL *{url}* loaded successfully.", icon="✅")


def load_corpus_to_db():
    """Index the Moroccan legal codes shipped in ./corpus (one click demo)."""
    pdfs = sorted(CORPUS_DIR.glob("*.pdf"))
    docs = []
    for pdf in pdfs:
        if pdf.name in st.session_state.rag_sources:
            continue
        try:
            loaded = PyPDFLoader(str(pdf)).load()
            for d in loaded:
                d.metadata["source"] = pdf.name
            docs.extend(loaded)
            st.session_state.rag_sources.append(pdf.name)
        except Exception as e:
            st.toast(f"Error loading {pdf.name}: {e}", icon="⚠️")

    if docs:
        _split_and_load_docs(docs)
        st.toast(f"Moroccan legal corpus loaded ({len(pdfs)} codes).", icon="📚")


def _embeddings():
    if "AZ_OPENAI_API_KEY" not in os.environ:
        return OpenAIEmbeddings(api_key=st.session_state.openai_api_key)
    return AzureOpenAIEmbeddings(
        api_key=os.getenv("AZ_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZ_OPENAI_ENDPOINT"),
        model="text-embedding-3-large",
        openai_api_version="2024-02-15-preview",
    )


def initialize_vector_db(document_chunks):
    vector_db = Chroma.from_documents(
        documents=document_chunks,
        embedding=_embeddings(),
        collection_name=f"{str(time()).replace('.', '')[:14]}_" + st.session_state["session_id"],
    )

    # Keep only the most recent collections in memory
    chroma_client = vector_db._client
    collection_names = sorted(collection.name for collection in chroma_client.list_collections())
    while len(collection_names) > MAX_COLLECTIONS_IN_MEMORY:
        chroma_client.delete_collection(collection_names.pop(0))

    return vector_db


def _split_and_load_docs(docs):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    document_chunks = text_splitter.split_documents(docs)

    # Normalise citation metadata: PyPDF pages are 0-indexed, web pages and
    # text files have no page at all.
    for chunk in document_chunks:
        page = chunk.metadata.get("page")
        chunk.metadata["page"] = page + 1 if isinstance(page, int) else "n/a"
        chunk.metadata.setdefault("source", "unknown")

    # Bug fix: the first load used to index the raw, unsplit documents.
    if st.session_state.get("vector_db") is None:
        st.session_state.vector_db = initialize_vector_db(document_chunks)
    else:
        st.session_state.vector_db.add_documents(document_chunks)


# --- Retrieval Augmented Generation (RAG) Phase ---

SYSTEM_PROMPT = """You are an assistant that answers questions about Moroccan law.
Answer ONLY from the context below. Every factual claim must cite its source
in brackets, using the file name and page, e.g. [code_famille.pdf, p. 12].
If the context does not contain the answer, say so clearly and suggest which
official text or professional to consult. Do not invent articles or numbers.
Answer in the language of the question (French, Arabic or English).
End with: "Information only, not legal advice."

Context:
{context}"""

# Each retrieved chunk is shown with its origin so the model can cite it.
DOCUMENT_PROMPT = PromptTemplate.from_template("[{source}, p. {page}]\n{page_content}")


def _get_context_retriever_chain(vector_db, llm):
    retriever = vector_db.as_retriever(search_kwargs={"k": 5})
    prompt = ChatPromptTemplate.from_messages([
        MessagesPlaceholder(variable_name="messages"),
        ("user", "{input}"),
        ("user", "Given the above conversation, generate a search query to look up in order to get information relevant to the conversation, focusing on the most recent messages."),
    ])
    return create_history_aware_retriever(llm, retriever, prompt)


def get_conversational_rag_chain(llm):
    retriever_chain = _get_context_retriever_chain(st.session_state.vector_db, llm)

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="messages"),
        ("user", "{input}"),
    ])
    stuff_documents_chain = create_stuff_documents_chain(
        llm,
        prompt,
        document_prompt=DOCUMENT_PROMPT,
    )
    return create_retrieval_chain(retriever_chain, stuff_documents_chain)


def stream_llm_rag_response(llm_stream, messages):
    conversation_rag_chain = get_conversational_rag_chain(llm_stream)
    response_message = "*(RAG Response)*\n"
    for chunk in conversation_rag_chain.pick("answer").stream({"messages": messages[:-1], "input": messages[-1].content}):
        response_message += chunk
        yield chunk

    st.session_state.messages.append({"role": "assistant", "content": response_message})
