
## Moroccan Legal Assistant RAG (Streamlit)

An AI‑powered **Moroccan legal assistant** built with **Python**, **Streamlit**, and **LangChain**.  
You can chat with **documents** and **websites** about Moroccan law using a Retrieval‑Augmented Generation (RAG) pipeline.

---

### Features

- **Moroccan law focus**: Ask questions and ground answers in uploaded Moroccan legal documents or web pages.
- **RAG pipeline**: Combines a vector store (Chroma) with OpenAI / Azure OpenAI models for context‑aware answers.
- **Multiple sources**:
  - Upload PDFs, DOCX, TXT, or Markdown files.
  - Provide URLs to scrape and index website content.
- **Streamlit UI**:
  - Sidebar for model selection and RAG settings.
  - Chat interface with history and optional RAG answers.

---

### Project Structure

- `app.py` – Main Streamlit app (UI, chat loop, model selection, sidebar).
- `rag_methods.py` – RAG utilities:
  - Loading documents/URLs.
  - Chunking and embedding.
  - Building and querying the Chroma vector database.
  - RAG‑style streaming responses.
- `rag_langchain.ipynb` – Notebook for experimentation and prototyping.
- `requirements.txt` – Python dependencies.
- `.env` – Local environment variables (NOT for Git; use `.env.example` as a template).
- `.env.example` – Example env file with placeholder keys.
- `.gitignore` – Ensures venv, `.env`, cache, and temp files are not committed.

Treat the `rag_llm_app` folder as the root of your GitHub repository.

---

### Environment Variables

This app uses `python-dotenv` to load variables from `.env` in the `rag_llm_app` directory.

Copy the example file:

```bash
cp .env.example .env
```

Then edit `.env` and fill in your own keys:

```env
OPENAI_API_KEY="your-openai-api-key-here"

# Azure OpenAI (optional, used if AZ_OPENAI_API_KEY is set)
AZ_OPENAI_ENDPOINT="https://your-azure-openai-resource.openai.azure.com/"
AZ_OPENAI_API_KEY="your-azure-openai-api-key-here"
```

**Security note**:  
Never commit `.env` with real keys to GitHub. The `.gitignore` in this project already ignores `.env`.

Also, because real keys were previously stored in `.env`, you should **rotate/regenerate** those keys in your OpenAI and Azure dashboards before making this repository public.

---

### Installation & Local Run

From inside the `rag_llm_app` folder:

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create and configure your .env file
cp .env.example .env
# edit .env and paste your own API keys

# 4. Run the Streamlit app
streamlit run app.py
```

Open the URL shown in the terminal (usually `http://localhost:8501`) to use the app.

---

### How the App Works (High Level)

1. **User provides data**
   - Uploads documents or enters a URL in the sidebar.
2. **Indexing**
   - `rag_methods.py`:
     - Loads documents or web pages.
     - Splits them into chunks with `RecursiveCharacterTextSplitter`.
     - Embeds chunks using OpenAI or Azure OpenAI embeddings.
     - Stores embeddings in a Chroma vector database.
3. **Chat / RAG**
   - In `app.py`, the user chats via the Streamlit chat UI.
   - If RAG is enabled:
     - The question + chat history are used to create a search query.
     - Relevant chunks are retrieved from Chroma.
     - The LLM generates an answer using these chunks as context.
   - Responses are streamed back to the UI.

---

### Preparing for GitHub

- **Recommended repo root**: use the `rag_llm_app` directory as the root of your GitHub repository.
- **Do NOT commit**:
  - `venv/` (virtual environment)
  - `.env` (real secrets)
  - `__pycache__/`, temporary files, or local DB files
- **Already handled** by `.gitignore`:
  - Virtual environments, `.env`, caches, and other common artefacts.

You can now safely initialize a git repo in this folder and push to GitHub:

```bash
cd rag_llm_app
git init
git add .
git commit -m "Initial commit: Moroccan Legal Assistant RAG"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

---

### Disclaimer

This application is built as a **capstone project** and is intended for **educational and research purposes only**.  
It is **not** a substitute for professional legal advice. Always verify outputs against official Moroccan legal sources or consult a qualified lawyer.
