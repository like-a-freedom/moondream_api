from pydantic import BaseModel


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
    content: str | list[ContentPartImage | ContentPartText]


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    temperature: float | None = 1.0
    stream: bool | None = False


class ChatChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatChoice]
    usage: dict[str, int]


class OllamaMessage(BaseModel):
    role: str
    content: str | list[dict[str, object]]
    images: list[str] | None = None


class OllamaChatRequest(BaseModel):
    model: str | None = None
    messages: list[OllamaMessage]
    stream: bool = False
    temperature: float | None = None
    max_tokens: int | None = None


class OllamaChatResponse(BaseModel):
    model: str
    created_at: str
    message: OllamaMessage
    done: bool


class OllamaShowModelRequest(BaseModel):
    model: str


class OllamaModelDetails(BaseModel):
    parent_model: str
    format: str
    family: str
    families: list[str]
    parameter_size: str
    quantization_level: str


class OllamaModelShowResponse(BaseModel):
    license: str
    modelfile: str
    parameters: str
    template: str
    details: OllamaModelDetails
    model_info: dict[str, object]
    projector_info: dict[str, object]
    modified_at: str


class OllamaGenerateOptions(BaseModel):
    num_keep: int | None = 5
    seed: int | None = 42
    num_predict: int | None = 100
    top_k: int | None = 20
    top_p: float | None = 0.9
    min_p: float | None = 0.0
    typical_p: float | None = 0.7
    repeat_last_n: int | None = 33
    temperature: float | None = 0.8
    repeat_penalty: float | None = 1.2
    presence_penalty: float | None = 1.5
    frequency_penalty: float | None = 1.0
    mirostat: int | None = 1
    mirostat_tau: float | None = 0.8
    mirostat_eta: float | None = 0.6
    penalize_newline: bool | None = True
    stop: list[str] | None = ["\\n", "user:"]
    numa: bool | None = False
    num_ctx: int | None = 1024
    num_batch: int | None = 2
    num_gpu: int | None = 1
    main_gpu: int | None = 0
    low_vram: bool | None = False
    vocab_only: bool | None = False
    use_mmap: bool | None = True
    use_mlock: bool | None = False
    num_thread: int | None = 8


class OllamaGenerateRequest(BaseModel):
    model: str
    prompt: str
    stream: bool | None = False
    options: OllamaGenerateOptions | None = OllamaGenerateOptions()
    images: list[str] | None = None


class OllamaGenerateResponse(BaseModel):
    model: str
    created_at: str
    response: str
    done: bool
    context: list[int]
    total_duration: int
    load_duration: int
    prompt_eval_count: int
    prompt_eval_duration: int
    eval_count: int
    eval_duration: int
