## Overview
The `moondream_api` project is designed to provide a lightweight and simple  OpenAI and Ollama-complaint API for handling various tasks. My goal was to make API for my own homeassistant + frigate bundle to integrate CV cameras with vision LLM that would be describe CV camera shots in a human-readable way. Service based on [Moondream](https://github.com/vikhyat/moondream) model that could be user even on Raspberry Pi/Orange Pi consumer-grade hardware.

## Features
- OpenAI and Ollama-complaint API (`/api/chat`, `/v1/api/completions`)
- Easy to integrate and use

## Usage Instructions
1. Clone the repository or just download the `docker-compose.yml` file.
2. Run the following command to start the service: `docker compose up -d`.
3. The service will be available at `http://localhost:18000` by default.
4. That's it! You can now start using the API.

**Notes**: 

1. First start, it will take some time to download the model and start the service (depends on your internet connection, need to download ~600 MB for 500M model).
2. In case if you're getting error like
```
Traceback (most recent call last):
  File "/app/src/vision_service.py", line 30, in _download_model
    os.makedirs(model_dir, exist_ok=True)
  File "<frozen os>", line 225, in makedirs
PermissionError: [Errno 13] Permission denied: '/app/model_cache/HuggingFaceTB_SmolVLM-256M-Instruct'
```
Then you need to change the permissions of the `model_cache` directory. You can do this by running the following command:
```
# Create the directory if it doesn't exist
mkdir -p ./model_cache

# Set permissions (replace 1000:1000 with your actual UID:GID)
sudo chown -R 1000:1000 ./model_cache
sudo chmod -R 755 ./model_cache
```

3. If you want to build the image yourself, you can run the following command: `docker compose up -d --build`.

## What else?

### Prompting

Default prompt is described in `src/config.py` file in `DEFAULT_PROMPT` constant. You can change it to your own needs. Another way is to pass the prompt as a query parameter in the request.

### API Endpoints and examples

FastAPI provides a nice interactive documentation for the API. You can access it at `http://localhost:18000/docs` or `http://localhost:18000/redoc`.

## Contributing
We welcome contributions from the community! If you would like to contribute to the project, please open an issue or submit a pull request.

## License
This project is licensed under the MIT. See the LICENSE file for more details.