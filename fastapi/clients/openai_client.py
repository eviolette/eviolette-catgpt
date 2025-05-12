import json
import re
import textwrap
import openai
import yaml
import logging
import tiktoken
from typing import List, Dict, Optional, Union
from enum import Enum
from pydantic import BaseModel, field_validator
from tenacity import retry, stop_after_attempt, wait_exponential


class OpenAIEnv(str, Enum):
    DEV = "dev"


class OpenAIConfig(BaseModel):
    env: OpenAIEnv
    api_key: str
    model: str
    temperature: float
    max_tokens_per_message: int
    max_tokens_per_chat: int

    @classmethod
    def from_yaml(cls, path: str) -> "OpenAIConfig":
        with open(path, "r") as f:
            config = yaml.safe_load(f)
        return cls(**config)

    @field_validator("api_key", "model")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field must not be empty.")
        return v


class OpenAIClient:
    def __init__(self, config_path: str):
        self._config = OpenAIConfig.from_yaml(config_path)

        self._client = openai.OpenAI(api_key=self._config.api_key)

        self._logger = logging.getLogger(__name__)

    @property
    def client(self) -> Union[openai.OpenAI, openai.AzureOpenAI]:
        return self._client

    @property
    def model(self) -> str:
        return self._config.model

    @property
    def max_tokens_per_message(self) -> int:
        return self._config.max_tokens_per_message

    @property
    def max_tokens_per_chat(self) -> int:
        return self._config.max_tokens_per_chat

    def _log_error(self, error: Exception, context: str = "") -> None:
        self._logger.error(f"OpenAIClient Error in {context}: {str(error)}")

    def _count_tokens(self, text: str, model: Optional[str] = None) -> int:
        encoding = tiktoken.encoding_for_model(model or self.model)
        return len(encoding.encode(text))

    def token_count_for_message(self, message: Dict[str, str], model: Optional[str] = None) -> int:
        content = message.get("content", "")
        return self._count_tokens(content, model)

    def token_count_for_chat(self, messages: List[Dict[str, str]], model: Optional[str] = None) -> int:
        return sum(self.token_count_for_message(m, model) for m in messages)

    def is_near_limit_message(self, message: Dict[str, str]) -> bool:
        return self.token_count_for_message(message) > 0.9 * self.max_tokens_per_message

    def is_near_limit_chat(self, messages: List[Dict[str, str]]) -> bool:
        return self.token_count_for_chat(messages) > 0.9 * self.max_tokens_per_chat

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=10))
    def get_json(
        self,
        prompt: str,
        output_struct: dict,  # should be JSON schema dict
        role: str = "user",
        messages: Optional[List[Dict[str, str]]] = None,
    ) -> Dict:
        try:
            messages = messages or []
            messages.append({"role": role, "content": prompt})

            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format=output_struct,
                temperature=self._config.temperature,
                max_tokens=self.max_tokens_per_message
            )

            return response.choices[0].message.content  # Parsed JSON will be here
        except Exception as e:
            self._log_error(e, "get_json")
            self._teardown()
            raise

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=10))
    def get_tool_calls(
        self,
        prompt: str,
        tools: List[Dict],
        role: str = "user",
        messages: Optional[List[Dict[str, str]]] = None,
    ) -> List[Dict]:
        try:
            messages = messages or []
            messages.append({"role": role, "content": prompt})
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens_per_message,
                tools=tools,
                temperature=self._config.temperature
            )
            return completion.choices[0].message.tool_calls
        except Exception as e:
            self._log_error(e, "get_tool_calls")
            raise

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=10))
    def get_text(
        self,
        prompt: str,
        role: str = "user",
        messages: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        try:
            messages = messages or []
            messages.append({"role": role, "content": prompt})
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens_per_message,
                temperature=self._config.temperature
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            self._log_error(e, "get_text")
            raise

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=10))
    def get_python(
        self,
        prompt: str,
        role: str = "user",
        messages: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        try:
            messages = messages or []
            messages.append({"role": role, "content": prompt})
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens_per_message,
                temperature=self._config.temperature
            )
            res = completion.choices[0].message.content.strip()
            formatted_text = textwrap.dedent(res).strip()
            cleaned_text = re.sub(
                pattern=r"^```[a-z]*\s*|```$",
                repl="", 
                string=formatted_text.strip(), 
                flags=re.IGNORECASE | re.MULTILINE).strip()
            return cleaned_text
        except Exception as e:
            self._log_error(e, "get_text")
            raise

    def _teardown(self):
        self._client = None

    def format_messages(self, messages: List[Dict[str, str]], max_length: int = 1000) -> str:
        """
        Return a pretty-formatted string of OpenAI messages.

        Args:
            messages: List of chat messages.
            max_length: Max content length per message (truncated if longer).

        Returns:
            A string that can be logged.
        """
        if not messages:
            return "No messages to display."

        formatted = []
        for i, msg in enumerate(messages):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            # Attempt to pretty-print JSON content
            if isinstance(content, str) and (content.strip().startswith("{") or content.strip().startswith("[")):
                try:
                    parsed = json.loads(content)
                    content = json.dumps(parsed, indent=2)
                except Exception:
                    pass  # leave raw content

            # Truncate if too long
            if len(content) > max_length:
                content = content[:max_length] + "... [truncated]"

            formatted.append(f"[{i+1}] {role}:\n{textwrap.indent(content, '  ')}")

        return "\n---\n".join(formatted)