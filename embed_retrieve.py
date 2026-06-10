import os
import glob
from sentence_transformers import SentenceTransformer
import chromadb

# 1. Configuration
CLEAN_DIR = "./documents/clean/"
CHROMA_DB_DIR = "./chroma_db"
COLLECTION_NAME = "ucla_neuroscience_guide"

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200
TOP_K = 4

# Test queries based on your UCLA Neuroscience domain
TEST_QUERIES = [
    "What are the major requirements for a neuroscience degree at UCLA?",
    "Does professor William Grisham or Stephanie White have good reviews?",
    "What advice do freshman neuroscience students get about their first quarter classes?"
]

# 2. Re-chunking helper (ensuring consistency with Milestone 3)
def chunk_text(text, chunk_size, overlap):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

# 3. Pipeline Implementation
def build_vector_store():
    """Loads cleaned text files, generates local embeddings, and stores them in ChromaDB."""
    print("Initializing local embedding model: all-MiniLM-L6-v2...")
    # Load the recommended SentenceTransformer model locally
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    print(f"Connecting to persistent ChromaDB at: {CHROMA_DB_DIR}")
    # Create a persistent database on disk so data is saved between runs
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    
    # Create or fetch the collection
    # collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)
    collection = chroma_client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"} # Forces Chroma to use Cosine distance
)
    
    # Gather all cleaned files from the previous step
    clean_files = glob.glob(os.path.join(CLEAN_DIR, "doc_*_clean.txt"))
    if not clean_files:
        print(f"No cleaned files found in {CLEAN_DIR}. Please run your ingestion script first!")
        return

    print(f"Found {len(clean_files)} documents. Processing chunks and embeddings...")
    
    all_chunks = []
    all_embeddings = []
    all_metadata = []
    all_ids = []
    
    global_chunk_counter = 0
    
    for file_path in sorted(clean_files):
        doc_name = os.path.basename(file_path)
        
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
            
        # Segment into chunks matching planning.md spec
        doc_chunks = chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
        
        # for position, chunk in enumerate(doc_chunks):
        #     # Generate local embedding vectors
        #     embedding = model.encode(chunk).tolist()
            
        #     all_chunks.append(chunk)
        for position, chunk in enumerate(doc_chunks):
            # Make a clean human-readable label from the filename
            context_label = doc_name.replace("doc_", "").replace("_clean.txt", "").replace("_", " ").title()
            
            # Prepend this context straight into the text block before embedding
            contextualized_chunk = f"Source Document: {context_label} | Content: {chunk}"
            
            # Embed the chunk WITH its context header
            embedding = model.encode(contextualized_chunk).tolist()
            
            all_chunks.append(contextualized_chunk) # Store the contextualized version
            all_embeddings.append(embedding)
            # Track source information for downstream LLM attribution
            all_metadata.append({
                "source_document": doc_name,
                "chunk_position": position
            })
            all_ids.append(f"id_{global_chunk_counter}")
            global_chunk_counter += 1

    # Upsert data into ChromaDB
    print(f"Adding {len(all_chunks)} total chunks to ChromaDB...")
    collection.add(
        ids=all_ids,
        embeddings=all_embeddings,
        documents=all_chunks,
        metadatas=all_metadata
    )
    print("Vector database build complete!\n")

def retrieve_context(query, k=TOP_K):
    """Embeds the user query and retrieves top-k matching documents from ChromaDB."""
    model = SentenceTransformer("all-MiniLM-L6-v2")
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    collection = chroma_client.get_collection(name=COLLECTION_NAME)
    
    # The query must be converted into the exact same vector space as the documents
    query_embedding = model.encode(query).tolist()
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k
    )
    return results

# 4. Main Execution and Evaluation
if __name__ == "__main__":
    # Step A: Build/Update the Vector Store
    build_vector_store()
    
    # Step B: Test and Evaluate with Queries
    print("="*60)
    print("EVALUATION: Testing Semantics & Retrieval")
    print("="*60)
    
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\nQuery {i}: \"{query}\"")
        print("-" * 50)
        
        retrieved = retrieve_context(query, k=TOP_K)
        
        # Unpack ChromaDB response lists (Chroma returns lists of lists)
        documents = retrieved['documents'][0]
        metadatas = retrieved['metadatas'][0]
        distances = retrieved['distances'][0]
        
        for idx in range(len(documents)):
            print(f"Match {idx+1} | Source: {metadatas[idx]['source_document']} (Chunk pos: {metadatas[idx]['chunk_position']})")
            print(f"Distance Score: {distances[idx]:.4f} (Lower = closer match)")
            # Print a brief preview of the chunk content
            preview = documents[idx][:150].strip().replace('\n', ' ')
            print(f"Content Preview: {preview}...")
            print("-" * 30)