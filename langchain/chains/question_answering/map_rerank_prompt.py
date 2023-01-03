# flake8: noqa
from langchain.prompts import PromptTemplate
from langchain.prompts.base import RegexParser

output_parser = RegexParser(
    regex=r"(.*?)\nScore: (.*)",
    output_keys=["answer", "score"],
)

prompt_template = """Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.

In addition to giving an answer, also return a score of how fully it answered the user's question. This should be in the following format:

Question: [question here]
Helpful Answer: [answer here]
Score: [score between 0 and 100]

How to determine the score:
- Higher is better
- Better responds fully to the asked question, with lots of detail
- If you do not know the answer based on the context, that should be a score of 0
- Don't be overconfident!

Begin! Use this context:

---------
{context}
---------

Question: {question}
Helpful Answer:"""
PROMPT = PromptTemplate(
    template=prompt_template,
    input_variables=["context", "question"],
    output_parser=output_parser,
)