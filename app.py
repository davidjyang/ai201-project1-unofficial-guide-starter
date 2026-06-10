import os
import gradio as gr
from groq import Groq
from dotenv import load_dotenv

# Import your retrieval function from the previous milestone script
from embed_retrieve import retrieve_context

# 1. Configuration & Initialization
load_dotenv() # Loads the GROQ_API_KEY from your .env file

# Initialize the Groq client. It will automatically look for the GROQ_API_KEY environment variable.
client = Groq() 
MODEL_NAME = "llama-3.3-70b-versatile"

# 2. Prompt Engineering
def build_prompt(question, context_chunks):
    """Constructs the prompt enforcing strict grounding rules."""
    # Combine the retrieved chunks into a single readable block for the LLM
    context_text = "\n\n---\n\n".join(context_chunks)
    
    prompt = f"""You are a helpful academic assistant for UCLA Neuroscience students. 
Answer the user's question using ONLY the information provided in the Context Documents below. 

Strict Rules:
- If the documents do not contain enough information to fully answer the question, explicitly say "I don't have enough information on that." 
- Do not use any outside knowledge.
- Do not hallucinate or guess.
- Keep your answer clear, direct, and conversational.

Context Documents:
{context_text}

User Question:
{question}

Answer:"""
    return prompt

def generate_answer(prompt):
    """Sends the grounded prompt to Groq's API."""
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model=MODEL_NAME,
        temperature=0.1, # A low temperature ensures factual consistency and reduces hallucinations
    )
    return chat_completion.choices[0].message.content

# 3. Pipeline Integration
def ask(question):
    """The main RAG pipeline: Retrieve -> Prompt -> Generate -> Attribute."""
    # Step A: Retrieve relevant chunks (importing your k=4 logic from Milestone 4)
    retrieved = retrieve_context(question)
    
    # Extract the actual text and metadata from ChromaDB's nested response lists
    documents = retrieved['documents'][0]
    metadatas = retrieved['metadatas'][0]
    
    # Step B: Programmatic Source Attribution
    # We use a set() to automatically remove duplicate source names if multiple chunks came from the same file
    # unique_sources = set()
    # for meta in metadatas:
    #     source_name = meta.get('source_document', 'Unknown Source')
    #     # Clean up the filename for better UI display (optional)
    #     clean_name = source_name.replace("doc_", "").replace("_clean.txt", " ").title()
    #     unique_sources.add(clean_name)
    URL_MAPPING = {
        "doc_1_clean.txt": "https://www.reddit.com/r/ucla/comments/heshap/a_little_neuroscience_advice/",
        "doc_2_clean.txt": "https://www.reddit.com/r/ucla/comments/1tx4w7h/recommended_first_quarter_freshman_classes_for/",
        "doc_3_clean.txt": "https://www.reddit.com/r/ucla/comments/1siadcz/ucla_neuro_students_how_is_it/",
        "doc_4_clean.txt": "https://www.neurosci.ucla.edu/faculty/",
        "doc_5_clean.txt": "https://www.neurosci.ucla.edu/program/major-requirements/",
        "doc_6_clean.txt": "https://www.neurosci.ucla.edu/program/minor-requirements/",
        "doc_7_clean.txt": "https://www.neurosci.ucla.edu/program/major-capstone/",
        "doc_8_clean.txt": "https://www.bruinwalk.com/professors/natik-piri/all/",
        "doc_9_clean.txt": "https://www.bruinwalk.com/professors/william-grisham/",
        "doc_10_clean.txt": "https://www.bruinwalk.com/professors/stephanie-a-white/"
    }

    unique_sources = set()
    for meta in metadatas:
        source_file = meta.get('source_document', '')
        # Retrieve the URL if it exists, otherwise fall back to a styled filename
        source_url = URL_MAPPING.get(source_file, source_file.replace("doc_", "").replace("_clean.txt", "").title())
        unique_sources.add(source_url)


    
    # Step C: Generation
    prompt = build_prompt(question, documents)
    llm_answer = generate_answer(prompt)
    
    return {
        "answer": llm_answer,
        "sources": list(unique_sources)
    }

# 4. Gradio UI Skeleton
def handle_query(question):
    """Wrapper function to map the pipeline output to the Gradio textboxes."""
    # Prevent empty queries from breaking the logic
    if not question.strip():
        return "Please enter a question.", ""
        
    result = ask(question)
    # Format the sources list with bullet points programmatically
    sources_formatted = "\n".join(f"• {s}" for s in result["sources"])
    
    return result["answer"], sources_formatted

# Build the Web Interface
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🧠 UCLA Neuroscience RAG Assistant")
    gr.Markdown("Ask questions about major/minor requirements, faculty reviews, and classes based on compiled department data.")
    
    with gr.Row():
        inp = gr.Textbox(label="Your question", placeholder="E.g., What are the core upper division major requirements?")
    
    btn = gr.Button("Ask", variant="primary")
    
    with gr.Row():
        answer = gr.Textbox(label="Answer", lines=8, interactive=False)
        sources = gr.Textbox(label="Retrieved from", lines=4, interactive=False)
        
    # Bind the query handler to both the button click and the Enter key
    btn.click(handle_query, inputs=inp, outputs=[answer, sources])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources])

if __name__ == "__main__":
    # Launch the local web server
    demo.launch()