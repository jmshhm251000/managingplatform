import re
import time
import asyncio
from typing import List, Any, Tuple
from llama_index.llms.ollama import Ollama
from llama_index.core.query_engine import BaseQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.core.schema import NodeWithScore, QueryBundle
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import TokenTextSplitter
from ..data_processing import get_document_text, VectorStoreIndex
from .ingestion import prepare_documents
from .prompt import get_prompt_template


class Chatbot(BaseQueryEngine):
    """
    Custom query engine that retrieves relevant nodes and synthesizes a response based on the user query.
    """
    def __init__(self, model_name: str, DOCUMENT_ID, SCOPES, METADATA=False):
        # Retrieve documents from Google Docs API using provided document ID and scopes
        self.document = get_document_text(DOCUMENT_ID, SCOPES) or []
        self.llm = Ollama(model=model_name, request_timeout=120.0)
        self.embed_model = HuggingFaceEmbedding(model_name="jhgan/ko-sbert-nli")

        if METADATA:
            if self.document:
                self.index = asyncio.get_event_loop().run_until_complete(
                    prepare_documents(self.document, self.sub_llm, self.embed_model)
                )
            else:
                self.index = VectorStoreIndex([], embed_model=self.embed_model)
        else:
            self.index = VectorStoreIndex(self.document if isinstance(self.document, list) else [], embed_model=self.embed_model)
        
        self.qa_template = get_prompt_template()
        self.retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=3,
        )
        self.response_synthesizer = get_response_synthesizer(llm=self.llm, text_qa_template=self.qa_template)


    def remove_think_blocks(self, response: str) -> Tuple[str, str]:
        """
        Extracts the content within <think> ... </think> blocks and returns a tuple containing:
        - The concatenated thinking block content.
        - The text with all <think> ... </think> blocks removed.
        """
        # Capture all text inside <think> and </think> using non-greedy matching (DOTALL ensures newlines are included)
        think_contents = re.findall(r"<think>(.*?)</think>", response, flags=re.DOTALL)
        
        # Combine multiple think blocks into one string, if necessary.
        thinking_block = "\n".join(think_contents)
        
        # Remove the <think> blocks from the original text.
        cleaned_text = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL).strip()
        # Remove the [EN] or [KR]
        cleaned_text_v2 = re.sub(r"\[[A-Z]{2}\]", "", cleaned_text).strip()
    
        return thinking_block, cleaned_text_v2


    def _query(self, query_str: str) -> Any:
        start_time = time.perf_counter()

        nodes: List[NodeWithScore] = self.retriever.retrieve(query_str)
        response = self.response_synthesizer.synthesize(query_str, nodes)

        think_block, final_response = self.remove_think_blocks(str(response.response))

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        elapsed_time_sec = round(elapsed_time, 4)

        return final_response


    async def _aquery(self, query_bundle: QueryBundle) -> Any:
        return self._query(query_bundle.query_str)


    def _get_prompt_modules(self) -> dict:
        return {}