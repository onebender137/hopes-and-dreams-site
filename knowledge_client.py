import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader, DirectoryLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

KNOWLEDGE_BASE_DIR = "knowledge_base"
VECTOR_DB_DIR = "vector_db"

class KnowledgeClient:
    def __init__(self):
        """Initializes the RAG-based Knowledge Client for Hopes and Dreams."""
        # Using a fast, local embedding model
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.vector_store = None
        
        if not os.path.exists(KNOWLEDGE_BASE_DIR):
            os.makedirs(KNOWLEDGE_BASE_DIR)
            
        self.load_or_build_index()

    def load_or_build_index(self):
        """Loads existing index or builds a new one from the knowledge_base folder."""
        if os.path.exists(VECTOR_DB_DIR) and os.listdir(VECTOR_DB_DIR):
            print("Loading existing knowledge index...")
            try:
                self.vector_store = FAISS.load_local(VECTOR_DB_DIR, self.embeddings, allow_dangerous_deserialization=True)
            except Exception as e:
                print(f"Error loading index: {e}. Rebuilding...")
                self.rebuild_index()
        else:
            self.rebuild_index()

    def rebuild_index(self):
        """Reads all files in knowledge_base and builds a new FAISS vector store."""
        print(f"Indexing all documents in {KNOWLEDGE_BASE_DIR}...")
        
        # Load PDFs and Text files
        pdf_loader = DirectoryLoader(KNOWLEDGE_BASE_DIR, glob="**/*.pdf", loader_cls=PyPDFLoader)
        txt_loader = DirectoryLoader(KNOWLEDGE_BASE_DIR, glob="**/*.txt", loader_cls=TextLoader)
        
        documents = pdf_loader.load() + txt_loader.load()
        
        if not documents:
            print("No documents found in knowledge_base to index.")
            return

        # Split documents into manageable chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_documents(documents)
        
        print(f"Split documents into {len(chunks)} chunks. Building vector store...")
        self.vector_store = FAISS.from_documents(chunks, self.embeddings)
        
        # Save for future use
        self.vector_store.save_local(VECTOR_DB_DIR)
        print("Knowledge index built and saved successfully.")

    def query_knowledge(self, query: str, limit: int = 3):
        """Retrieves the most relevant chunks from the local knowledge base."""
        if not self.vector_store:
            return ""
            
        print(f"Querying knowledge base for: {query}...")
        results = self.vector_store.similarity_search(query, k=limit)
        
        context = "\n---\n".join([doc.page_content for doc in results])
        return context

if __name__ == "__main__":
    # Test Knowledge Client
    # Create a dummy file if knowledge_base is empty
    if not os.listdir(KNOWLEDGE_BASE_DIR):
        with open(os.path.join(KNOWLEDGE_BASE_DIR, "intro.txt"), "w") as f:
            f.write("Hopes and Dreams is a biohacking syndicate focused on high-performance supplements like Nicotine, Kratom, and Magnesium.")
            
    client = KnowledgeClient()
    print("Query Result:", client.query_knowledge("What is Hopes and Dreams?"))
