# Weaviate

This page covers how to use the Weaviate ecosystem within LangChain.
It is broken into two parts: installation and setup, and then references to specific Pinecone wrappers.

## Installation and Setup
- Install the Python SDK with `pip install weaviate-client`
## Wrappers

### VectorStore

There exists a wrapper around Weaviate indexes, allowing you to use it as a vectorstore,
whether for semantic search or example selection.

To import this vectorstore:
```python
from langchain.vectorstores import Weaviate
```

For a more detailed walkthrough of the Weaviate wrapper, see [this notebook](../modules/utils/combine_docs_examples/vectorstores.ipynb)