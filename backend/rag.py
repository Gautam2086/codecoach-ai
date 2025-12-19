"""
RAG pipeline using FAISS + LangChain.
Retrieves relevant chunks from CTCI Arrays & Strings chapter.

Uses HuggingFace embeddings (free, runs locally).
Docs: https://python.langchain.com/docs/integrations/vectorstores/faiss
"""

import logging
from pathlib import Path
from typing import List, Tuple, Optional

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("codecoach.rag")

DATA_DIR = Path(__file__).parent / "data"
INDEX_PATH = DATA_DIR / "faiss_index"
PDF_PATH = DATA_DIR / "ctci_arrays_strings.pdf"


class RAGPipeline:
    
    def __init__(self):
        logger.info("Loading OpenAI embeddings...")
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.vectorstore: Optional[FAISS] = None
        self.is_initialized = False
    
    def initialize(self) -> bool:
        # Loading existing index or building from PDF
        try:
            if INDEX_PATH.exists():
                logger.info("Loading FAISS index...")
                self.vectorstore = FAISS.load_local(
                    str(INDEX_PATH), 
                    self.embeddings,
                    allow_dangerous_deserialization=True  # Required for pickle
                )
            elif PDF_PATH.exists():
                logger.info("Building FAISS index from PDF...")
                self._build_from_pdf()
            else:
                logger.warning(f"No FAISS index at {INDEX_PATH} or PDF at {PDF_PATH}")
                return False
            
            self.is_initialized = True
            return True
        except Exception as e:
            logger.error(f"Init failed: {e}")
            return False
    
    def _build_from_pdf(self) -> None:
        # Extracting text, chunking, embedding & saving the index
        loader = PyPDFLoader(str(PDF_PATH))
        docs = loader.load()
        logger.info(f"Loaded {len(docs)} pages")
        
        # Chunking the text into smaller chunks for precise retrieval
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        chunks = splitter.split_documents(docs)
        
        # Adding chunk IDs for observability
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_id"] = f"chunk_{i}"
        
        logger.info(f"Created {len(chunks)} FAISS chunks")
        
        self.vectorstore = FAISS.from_documents(chunks, self.embeddings)
        # Creating the data directory if it doesn't exist
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        # Saving the index to the data directory
        self.vectorstore.save_local(str(INDEX_PATH))
        logger.info("Index saved")
    
    def retrieve(self, query: str, k: int = 3) -> str:
        # Retrieving the top-k chunks with logging
        if not self.vectorstore:
            return ""
        
        results: List[Tuple[Document, float]] = (
            self.vectorstore.similarity_search_with_score(query, k=k)
        )
        
        # Logging the results for observability
        logger.info(f"Query: '{query[:60]}...'")
        for i, (doc, score) in enumerate(results):
            chunk_id = doc.metadata.get("chunk_id", "?")
            page = doc.metadata.get("page", "?")
            logger.info(f"  #{i+1} chunk={chunk_id} page={page} score={score:.3f}")
        
        return "\n\n---\n\n".join(doc.page_content for doc, _ in results)
    
    def get_context_for_llm(self, query: str) -> str:
        # Formatting the retrieved context for LLM injection
        context = self.retrieve(query)
        if not context:
            return ""
        
        return f"""[CTCI Arrays & Strings context]
{context}
[End context - use this to answer accurately]"""


# Singleton RAG pipeline
_pipeline: Optional[RAGPipeline] = None

def get_rag_pipeline() -> RAGPipeline:
    # Getting or creating the RAG pipeline singleton
    global _pipeline
    if _pipeline is None:
        _pipeline = RAGPipeline()
        _pipeline.initialize()
    return _pipeline
