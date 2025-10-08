
from llm_service import list_models, chat


def test_list_models():
    """Test that list_models returns a list of model names."""
    models = list_models()
    assert isinstance(models, list), "Expected models to be a list"
    assert len(models) > 0, "Expected models list to be non-empty"
    print(f"Available models: {models}")


def test_chat_hi():
    """Test that we can send 'Hi!' to the LLM and get a response."""
    message = "Hi!"
    response = chat(message)
    
    # Check that we got some response
    assert isinstance(response, str), "Expected response to be a string"
    assert len(response) > 0, "Expected non-empty response"
    assert not response.startswith("Error:"), f"Got error response: {response}"
    
    print(f"User: {message}")
    print(f"LLM: {response}")
