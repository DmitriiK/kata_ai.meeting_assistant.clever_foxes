from openai import AzureOpenAI
import config as cfg

# Initialize the AzureOpenAI client
client = AzureOpenAI(
    api_version=cfg.AzureOpenAI.OPENAI_API_VERSION,
    azure_endpoint=cfg.AzureOpenAI.AZURE_OPENAI_ENDPOINT,  # type: ignore
    api_key=cfg.AzureOpenAI.AZURE_OPENAI_API_KEY,
)


def list_models():
    """Get list of available models from Azure OpenAI."""
    try:
        models = client.models.list()
        model_names = [model.id for model in models.data]
        return model_names
    except Exception as e:
        print(f"Error listing models: {e}")
        # Return a default model if API call fails (for testing purposes)
        return [cfg.AzureOpenAI.MODEL_NAME]


def chat(message: str, max_tokens: int = 300, temperature: float = 0.7) -> str:
    """Send a message to the LLM and get a response."""
    try:
        response = client.chat.completions.create(
            model=cfg.AzureOpenAI.MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful AI meeting assistant. Provide concise, actionable responses that help improve meeting productivity and understanding."},
                {"role": "user", "content": message}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        content = response.choices[0].message.content
        return content.strip() if content else "No response"
    except Exception as e:
        print(f"Error in chat: {e}")
        return f"Error: {str(e)}"

