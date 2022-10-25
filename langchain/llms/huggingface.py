"""Wrapper around HuggingFace APIs."""
import os
from typing import Any, Dict, List, Mapping, Optional

from pydantic import BaseModel, Extra, root_validator

from langchain.llms.base import LLM
from langchain.llms.utils import enforce_stop_tokens

DEFAULT_REPO_ID = "gpt2"


class HuggingFace(BaseModel, LLM):
    """Wrapper around HuggingFace large language models.

    To use, you should have the ``huggingface_hub`` python package installed, and the
    environment variable ``HUGGINGFACE_API_TOKEN`` set with your API token.

    Only supports task `text-generation` for now.

    Example:
        .. code-block:: python

            from langchain import HuggingFace
            hf = HuggingFace(model="text-davinci-002")
    """

    client: Any  #: :meta private:
    repo_id: str = DEFAULT_REPO_ID
    """Model name to use."""
    temperature: float = 0.7
    """What sampling temperature to use."""
    max_new_tokens: int = 200
    """The maximum number of tokens to generate in the completion."""
    top_p: int = 1
    """Total probability mass of tokens to consider at each step."""
    num_return_sequences: int = 1
    """How many completions to generate for each prompt."""

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid

    @root_validator()
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that api key and python package exists in environment."""
        if "HUGGINGFACE_API_TOKEN" not in os.environ:
            raise ValueError(
                "Did not find HuggingFace API token, please add an environment variable"
                " `HUGGINGFACE_API_TOKEN` which contains it."
            )
        try:
            from huggingface_hub.inference_api import InferenceApi

            repo_id = values.get("repo_id", DEFAULT_REPO_ID)
            values["client"] = InferenceApi(
                repo_id=repo_id,
                token=os.environ["HUGGINGFACE_API_TOKEN"],
                task="text-generation",
            )
        except ImportError:
            raise ValueError(
                "Could not import huggingface_hub python package. "
                "Please it install it with `pip install huggingface_hub`."
            )
        return values

    @property
    def _default_params(self) -> Mapping[str, Any]:
        """Get the default parameters for calling OpenAI API."""
        return {
            "temperature": self.temperature,
            "max_new_tokens": self.max_new_tokens,
            "top_p": self.top_p,
            "num_return_sequences": self.num_return_sequences,
        }

    def __call__(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        """Call out to HuggingFace Hub's inference endpoint.

        Args:
            prompt: The prompt to pass into the model.
            stop: Optional list of stop words to use when generating.

        Returns:
            The string generated by the model.

        Example:
            .. code-block:: python

                response = hf("Tell me a joke.")
        """
        response = self.client(inputs=prompt, params=self._default_params)
        if "error" in response:
            raise ValueError(f"Error raised by inference API: {response['error']}")
        text = response[0]["generated_text"][len(prompt) :]
        if stop is not None:
            text = enforce_stop_tokens(text, stop)
        return text
