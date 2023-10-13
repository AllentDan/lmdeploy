# Copyright (c) OpenMMLab. All rights reserved.
import json
from typing import Any, Dict, Iterable, List, Optional, Union

import fire
import requests


def get_model_list(api_url: str):
    response = requests.get(api_url)
    if hasattr(response, 'text'):
        model_list = json.loads(response.text)
        model_list = model_list.pop('data', [])
        return [item['id'] for item in model_list]
    return None


class APIClient:
    """Chatbot for LLaMA series models with turbomind as inference engine.

    Args:
        api_server_url (str): communicating address 'http://<ip>:<port>' of
            api_server
    """

    def __init__(self, api_server_url: str, **kwargs):
        self.api_server_url = api_server_url
        self.generate_url = f'{api_server_url}/generate'
        self.chat_completions_v1_url = f'{api_server_url}/v1/chat/completions'
        self.completions_v1_url = f'{api_server_url}/v1/completions'
        self.embeddings_v1_url = f'{api_server_url}/v1/embeddings'
        self.models_v1_url = f'{api_server_url}/v1/models'
        self._available_models = None
        self._rounds = {}

    @property
    def available_models(self):
        if self._available_models is not None:
            return self._available_models
        response = requests.get(self.models_v1_url)
        if hasattr(response, 'text'):
            model_list = json.loads(response.text)
            model_list = model_list.pop('data', [])
            self._available_models = [item['id'] for item in model_list]
            return self._available_models
        return None

    def chat_completions_v1(self,
                            model: str,
                            messages: Union[str, List[Dict[str, str]]],
                            temperature: Optional[float] = 0.7,
                            top_p: Optional[float] = 1.0,
                            n: Optional[int] = 1,
                            max_tokens: Optional[int] = 512,
                            stop: Optional[bool] = False,
                            stream: Optional[bool] = False,
                            presence_penalty: Optional[float] = 0.0,
                            frequency_penalty: Optional[float] = 0.0,
                            user: Optional[str] = None,
                            repetition_penalty: Optional[float] = 1.0,
                            session_id: Optional[int] = -1,
                            ignore_eos: Optional[bool] = False,
                            **kwargs):
        """Chat completion v1.

        Args:
            model: model name. Available from self.available_models.
            messages: string prompt or chat history in OpenAI format.
            temperature (float): to modulate the next token probability
            top_p (float): If set to float < 1, only the smallest set of most
                probable tokens with probabilities that add up to top_p or
                higher are kept for generation.
            n (int): How many chat completion choices to generate for each
                input message. Only support one here.
            stream: whether to stream the results or not. Default to false.
            max_tokens (int): output token nums
            repetition_penalty (float): The parameter for repetition penalty.
                1.0 means no penalty
            ignore_eos (bool): indicator for ignoring eos
            session_id (int): if not specified, will set random value

        Yields:
            json objects in openai formats
        """
        pload = {
            k: v
            for k, v in locals().copy().items()
            if k[:2] != '__' and k not in ['self']
        }
        headers = {'content-type': 'application/json'}
        response = requests.post(self.chat_completions_v1_url,
                                 headers=headers,
                                 json=pload,
                                 stream=stream)
        for chunk in response.iter_lines(chunk_size=8192,
                                         decode_unicode=False,
                                         delimiter=b'\n'):
            if chunk:
                if stream:
                    decoded = chunk.decode('utf-8')[6:]
                    if decoded == '[DONE]':
                        continue
                    output = json.loads(decoded)
                    yield output
                else:
                    decoded = chunk.decode('utf-8')
                    output = json.loads(decoded)
                    yield output

    def generate(self,
                 prompt: Union[str, List[Dict[str, str]]],
                 session_id: int = -1,
                 sequence_start: bool = True,
                 sequence_end: bool = True,
                 stream: bool = False,
                 stop: bool = False,
                 request_output_len: int = 512,
                 top_p: float = 0.8,
                 top_k: int = 40,
                 temperature: float = 0.8,
                 repetition_penalty: float = 1.0,
                 ignore_eos: bool = False,
                 **kwargs):
        """Generate.

        - On interactive mode, the chat history is kept on the server. Set
        `sequence_start = True` and `sequence_end = False` for the first
        request, Set `sequence_start = False` and `sequence_end = False` for
        the later requests. Once the session length limit is reached, set
        `sequence_start = False` and `sequence_end = True` to end the session.
        Then restart the above steps for a new session.

        - On normal mode, no chat history is kept on the server. Set
        `sequence_start = True` and `sequence_end = True` for all requests.

        Args:
            prompt: the prompt to use for the generation.
            session_id: determine which instance will be called.
                If not specified with a value other than -1, using random value
                directly.
            sequence_start (bool): a flag to start the session. Set True to
                start the session.
            sequence_end (bool): a flag to end the session. Set True to end the
                session.
            stream: whether to stream the results or not.
            stop: whether to stop the session response or not.
            request_output_len (int): output token nums
            step (int): the offset of the k/v cache
            top_p (float): If set to float < 1, only the smallest set of most
                probable tokens with probabilities that add up to top_p or
                higher are kept for generation.
            top_k (int): The number of the highest probability vocabulary
                tokens to keep for top-k-filtering
            temperature (float): to modulate the next token probability
            repetition_penalty (float): The parameter for repetition penalty.
                1.0 means no penalty
            ignore_eos (bool): indicator for ignoring eos

        Yields:
            json objects consist of text, tokens, finish_reason
        """
        pload = {
            k: v
            for k, v in locals().copy().items()
            if k[:2] != '__' and k not in ['self']
        }
        headers = {'content-type': 'application/json'}
        response = requests.post(self.generate_url,
                                 headers=headers,
                                 json=pload,
                                 stream=stream)
        for chunk in response.iter_lines(chunk_size=8192,
                                         decode_unicode=False,
                                         delimiter=b'\n'):
            if chunk:
                decoded = chunk.decode('utf-8')
                output = json.loads(decoded)
                yield output

    def completions_v1(
            self,
            model: str,
            prompt: Union[str, List[Any]],
            suffix: Optional[str] = None,
            temperature: Optional[float] = 0.7,
            n: Optional[int] = 1,
            max_tokens: Optional[int] = 16,
            stream: Optional[bool] = False,
            top_p: Optional[float] = 1.0,
            user: Optional[str] = None,
            # additional argument of lmdeploy
            repetition_penalty: Optional[float] = 1.0,
            session_id: Optional[int] = -1,
            ignore_eos: Optional[bool] = False,
            **kwargs):
        """Chat completion v1.

        Args:
            model (str): model name. Available from /v1/models.
            prompt (str): the input prompt.
            suffix (str): The suffix that comes after a completion of inserted
                text.
            max_tokens (int): output token nums
            temperature (float): to modulate the next token probability
            top_p (float): If set to float < 1, only the smallest set of most
                probable tokens with probabilities that add up to top_p or
                higher are kept for generation.
            n (int): How many chat completion choices to generate for each
                input message. Only support one here.
            stream: whether to stream the results or not. Default to false.
            repetition_penalty (float): The parameter for repetition penalty.
                1.0 means no penalty
            user (str): A unique identifier representing your end-user.
            ignore_eos (bool): indicator for ignoring eos
            session_id (int): if not specified, will set random value

        Yields:
            json objects in openai formats
        """
        pload = {
            k: v
            for k, v in locals().copy().items()
            if k[:2] != '__' and k not in ['self']
        }
        headers = {'content-type': 'application/json'}
        response = requests.post(self.completions_v1_url,
                                 headers=headers,
                                 json=pload,
                                 stream=stream)
        for chunk in response.iter_lines(chunk_size=8192,
                                         decode_unicode=False,
                                         delimiter=b'\n'):
            if chunk:
                if stream:
                    decoded = chunk.decode('utf-8')[6:]
                    if decoded == '[DONE]':
                        continue
                    output = json.loads(decoded)
                    yield output
                else:
                    decoded = chunk.decode('utf-8')
                    output = json.loads(decoded)
                    yield output

    def embeddings_v1(self,
                      model: str,
                      input: Union[str, List[Any]],
                      user: Optional[str] = None,
                      **kwargs):
        """Embeddings.

        Args:
            model (str): the model name.
            input (str): prompt or chat history.
            user (str): A unique identifier representing your end-user.

        Yields:
            json objects in openai formats
        """
        pload = dict(model=model, input=input, user=user)
        headers = {'content-type': 'application/json'}
        response = requests.post(self.embeddings_v1_url,
                                 headers=headers,
                                 json=pload)
        for chunk in response.iter_lines(chunk_size=8192,
                                         decode_unicode=False,
                                         delimiter=b'\n'):
            if chunk:
                decoded = chunk.decode('utf-8')
                output = json.loads(decoded)
                yield output

    def chat(self,
             prompt: str,
             session_id: int,
             request_output_len: int = 512,
             stream: bool = False,
             top_p: float = 0.8,
             top_k: int = 40,
             temperature: float = 0.8,
             repetition_penalty: float = 1.0,
             ignore_eos: bool = False):
        """Chat with a unique session_id.

        Args:
            prompt: the prompt to use for the generation.
            session_id: determine which instance will be called.
                If not specified with a value other than -1, using random value
                directly.
            stream: whether to stream the results or not.
            stop: whether to stop the session response or not.
            request_output_len (int): output token nums
            top_p (float): If set to float < 1, only the smallest set of most
                probable tokens with probabilities that add up to top_p or
                higher are kept for generation.
            top_k (int): The number of the highest probability vocabulary
                tokens to keep for top-k-filtering
            temperature (float): to modulate the next token probability
            repetition_penalty (float): The parameter for repetition penalty.
                1.0 means no penalty
            ignore_eos (bool): indicator for ignoring eos

        Yields:
            text, tokens, finish_reason
        """
        assert session_id != -1, 'please set other value other than -1'
        if str(session_id) not in self._rounds:
            self._rounds[str(session_id)] = 1
        for outputs in self.generate(
                prompt,
                session_id=session_id,
                request_output_len=request_output_len,
                sequence_start=(self._rounds[str(session_id)] == 1),
                sequence_end=False,
                stream=stream,
                top_k=top_k,
                top_p=top_p,
                temperature=temperature,
                repetition_penalty=repetition_penalty,
                ignore_eos=ignore_eos):
            if outputs['finish_reason'] == 'length':
                print('WARNING: exceed session max length.'
                      ' Please end the session.')
            yield outputs['text'], outputs['tokens'], outputs['finish_reason']
        self._rounds[str(session_id)] += 1

    def end_session(self, session_id: int):
        """End the session with a unique session_id.

        Args:
            session_id: determine which instance will be called.
                If not specified with a value other than -1, using random value
                directly.
        """
        self._rounds[str(session_id)] = 1
        for out in self.generate(prompt='',
                                 session_id=session_id,
                                 request_output_len=0,
                                 sequence_start=False,
                                 sequence_end=True):
            pass


def input_prompt():
    """Input a prompt in the consolo interface."""
    print('\ndouble enter to end input >>> ', end='')
    sentinel = ''  # ends when this string is seen
    return '\n'.join(iter(input, sentinel))


def get_streaming_response(prompt: str,
                           api_url: str,
                           session_id: int,
                           request_output_len: int = 512,
                           stream: bool = True,
                           sequence_start: bool = True,
                           sequence_end: bool = True,
                           ignore_eos: bool = False,
                           stop: bool = False) -> Iterable[List[str]]:
    headers = {'User-Agent': 'Test Client'}
    pload = {
        'prompt': prompt,
        'stream': stream,
        'session_id': session_id,
        'request_output_len': request_output_len,
        'sequence_start': sequence_start,
        'sequence_end': sequence_end,
        'ignore_eos': ignore_eos,
        'stop': stop
    }
    response = requests.post(api_url,
                             headers=headers,
                             json=pload,
                             stream=stream)
    for chunk in response.iter_lines(chunk_size=8192,
                                     decode_unicode=False,
                                     delimiter=b'\n'):
        if chunk:
            data = json.loads(chunk.decode('utf-8'))
            output = data.pop('text', '')
            tokens = data.pop('tokens', 0)
            finish_reason = data.pop('finish_reason', None)
            yield output, tokens, finish_reason


def main(api_server_url: str, session_id: int = 0):
    api_client = APIClient(api_server_url)
    while True:
        prompt = input_prompt()
        if prompt in ['exit', 'end']:
            api_client.end_session(session_id)
            if prompt == 'exit':
                exit(0)
        else:
            for text, tokens, finish_reason in api_client.chat(
                    prompt,
                    session_id=session_id,
                    request_output_len=512,
                    stream=True):
                if finish_reason == 'length':
                    continue
                print(text, end='')


if __name__ == '__main__':
    fire.Fire(main)
