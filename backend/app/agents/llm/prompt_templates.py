"""
Prompt Templates (LangChain)
==============================
Milestone 1 explicitly asks for "prompt templates" — this is LangChain's
`ChatPromptTemplate` abstraction, used here instead of building prompts as
raw Python f-strings. Centralizing them also means every agent's prompt
wording lives in one place, easy to review/tune independently of the
agent's decision logic.
"""
from langchain_core.prompts import ChatPromptTemplate

ROOT_CAUSE_PROMPT = ChatPromptTemplate.from_template(
    "An incident was detected on service '{service_name}'. "
    "Metrics: {raw_metrics}. Error signature: {error_signature}."
    "{memory_context}\n"
    "In 2 short sentences, explain the most likely root cause a DevOps engineer would suspect."
)

CONFLICT_RESOLUTION_PROMPT = ChatPromptTemplate.from_template(
    "Two developers, {dev_a_name} and {dev_b_name}, are both editing the function "
    "'{function_name}' in file '{file_path}' at the same time, which risks a merge conflict."
    "{memory_context}\n"
    "In 2 short sentences, suggest how they should coordinate to avoid losing each other's work."
)

TOOL_SELECTION_PROMPT = ChatPromptTemplate.from_template(
    "You are selecting the single best tool to handle this situation.\n"
    "Situation: {situation}\n\n"
    "Available tools:\n{tool_descriptions}\n\n"
    "Reply with ONLY the exact tool name from the list above, nothing else."
)
