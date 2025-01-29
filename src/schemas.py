from pydantic import BaseModel
from typing import Optional, Union, List, Dict


class ImageUrl(BaseModel):
    url: str

class ContentPartImage(BaseModel):
    type: str = "image_url"
    image_url: ImageUrl

class ContentPartText(BaseModel):
    type: str = "text"
    text: str

class ChatMessage(BaseModel):
    role: str
    content: Union[str, List[Union[ContentPartImage, ContentPartText]]]

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 1.0
    stream: Optional[bool] = False

class ChatChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatChoice]
    usage: Dict[str, int]


class OllamaMessage(BaseModel):
    role: str
    content: Union[str, List[dict]]
    images: Optional[List[str]] = None


class OllamaRequest(BaseModel):
    model: Optional[str] = None
    messages: List[OllamaMessage]
    stream: bool = False
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


class OllamaResponse(BaseModel):
    model: str
    created_at: str
    message: OllamaMessage
    done: bool
