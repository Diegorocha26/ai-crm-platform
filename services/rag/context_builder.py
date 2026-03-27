from services.rag.retriever import Retriever

class ContextBuilder:
    def __init__(self):
        self.retriever = Retriever()

    async def build_context(self, query: str, top_k: int = 3) -> str:
        """
        Retrieve chunks and format them into a clean context block for prompt injection.
        """
        results = await self.retriever.search(query, top_k=top_k)
        
        if not results:
            return ""
        
        context_parts = []
        for i, r in enumerate(results):
            payload = r.payload
            # Extract content
            name = payload.get("name", "Unknown")
            industry = payload.get("industry", "N/A")
            text = payload.get("profile_text", "")
            
            # If profile_text is missing, try to construct something
            if not text:
                text = f"{name} ({industry})"
            
            context_parts.append(f"Source {i+1}:\n{text}")
        
        # Join with clear delimiters
        full_context = "\n\n".join(context_parts)
        
        # Simple truncation if too long (rough token estimation 4 chars/token)
        # Limit to ~1000 tokens => 4000 chars
        if len(full_context) > 4000:
            full_context = full_context[:4000] + "... (truncated)"
            
        return full_context
