"""Chain that just formats a prompt and calls an LLM."""
from typing import Any, Dict, List, Union

from pydantic import BaseModel, Extra
import yaml
from pathlib import Path

import langchain
from langchain.chains.base import Chain
from langchain.llms.base import BaseLLM, LLMResult
from langchain.prompts.base import BasePromptTemplate


class LLMChain(Chain, BaseModel):
    """Chain to run queries against LLMs.

    Example:
        .. code-block:: python

            from langchain import LLMChain, OpenAI, PromptTemplate
            prompt_template = "Tell me a {adjective} joke"
            prompt = PromptTemplate(
                input_variables=["adjective"], template=prompt_template
            )
            llm = LLMChain(llm=OpenAI(), prompt=prompt)
    """

    prompt: BasePromptTemplate
    """Prompt object to use."""
    llm: BaseLLM
    """LLM wrapper to use."""
    output_key: str = "text"  #: :meta private:

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid
        arbitrary_types_allowed = True

    @property
    def input_keys(self) -> List[str]:
        """Will be whatever keys the prompt expects.

        :meta private:
        """
        return self.prompt.input_variables

    @property
    def output_keys(self) -> List[str]:
        """Will always return text key.

        :meta private:
        """
        return [self.output_key]

    def generate(self, input_list: List[Dict[str, Any]]) -> LLMResult:
        """Generate LLM result from inputs."""
        stop = None
        if "stop" in input_list[0]:
            stop = input_list[0]["stop"]
        prompts = []
        for inputs in input_list:
            selected_inputs = {k: inputs[k] for k in self.prompt.input_variables}
            prompt = self.prompt.format(**selected_inputs)
            if self.verbose:
                langchain.logger.log_llm_inputs(selected_inputs, prompt)
            if "stop" in inputs and inputs["stop"] != stop:
                raise ValueError(
                    "If `stop` is present in any inputs, should be present in all."
                )
            prompts.append(prompt)
        response = self.llm.generate(prompts, stop=stop)
        return response

    def apply(self, input_list: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Utilize the LLM generate method for speed gains."""
        response = self.generate(input_list)
        outputs = []
        for generation in response.generations:
            # Get the text of the top generated string.
            response_str = generation[0].text
            if self.verbose:
                langchain.logger.log_llm_response(response_str)
            outputs.append({self.output_key: response_str})
        return outputs

    def _call(self, inputs: Dict[str, Any]) -> Dict[str, str]:
        return self.apply([inputs])[0]

    def predict(self, **kwargs: Any) -> str:
        """Format prompt with kwargs and pass to LLM.

        Args:
            **kwargs: Keys to pass to prompt template.

        Returns:
            Completion from LLM.

        Example:
            .. code-block:: python

                completion = llm.predict(adjective="funny")
        """
        return self(kwargs)[self.output_key]

    def predict_and_parse(self, **kwargs: Any) -> Union[str, List[str], Dict[str, str]]:
        """Call predict and then parse the results."""
        result = self.predict(**kwargs)
        if self.prompt.output_parser is not None:
            return self.prompt.output_parser.parse(result)
        else:
            return result

    def save(self, file_path: Union[Path, str]) -> None:
        # Convert file to Path object.
        if isinstance(file_path, str):
            save_path = Path(file_path)
        else:
            save_path = file_path

        directory_path = save_path.parent
        directory_path.mkdir(parents=True, exist_ok=True)

        info_directory = self.dict()

        if self.memory is not None:
            raise ValueError("Saving Memory not Currently Supported.")
        del info_directory["memory"]

        # Save prompts and llms separately
        del info_directory["prompt"]
        del info_directory["llm"]

        prompt_file = directory_path / "llm_prompt.yaml"
        llm_file = directory_path / "llm.yaml"

        # Save these separately, so LLM, prompt loading is configurable
        # and not tied to chain itself
        info_directory["prompt_path"] = str(prompt_file)
        info_directory["llm_path"] = str(llm_file)
        info_directory["_type"] = "llm"

        # Save prompt and llm associated with LLM Chain
        self.prompt.save(prompt_file)
        self.llm.save(llm_file)

        with open(save_path, "w") as f:
            yaml.dump(info_directory, f, default_flow_style=False)
