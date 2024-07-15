import instructor

from openai import OpenAI
from pydantic import BaseModel, Field


class Triple(BaseModel):
    subject: str = Field(description="The subject of the triple")
    relation: str = Field(description="The relation of the triple")
    object: str = Field(description="The object of the triple")


class KnowledgeGraph(BaseModel):
    triples: list[Triple] = Field(description="List of triples in the knowledge graph")


def get_prompt_from_txt(path: str):
    with open(path, 'r') as f:
        prompt = f.read()
    return prompt

def create_knowledge_graph(prompt: str, model_name: str) -> KnowledgeGraph:
    client = instructor.from_openai(
        OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama",
        ),
        mode=instructor.Mode.JSON,
    )

    kg = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        response_model=KnowledgeGraph,
    )
    return kg

def compare_knowledge_graphs(model_name: str, kg1: KnowledgeGraph, kg2: KnowledgeGraph, original_prompt: str) -> KnowledgeGraph:
    prompt = f"""
    Compare the following two knowledge graphs and decide which one is more comprehensive and accurate.
    Consider the quality of assertions and their relevance to the original instructions and sentence.

    Instructions:
    {original_prompt}

    Knowledge Graph 1:
    {kg1.model_dump_json()}

    Knowledge Graph 2:
    {kg2.model_dump_json()}
    """

    final_kg = create_knowledge_graph(prompt=prompt, model_name=model_name)
    return final_kg