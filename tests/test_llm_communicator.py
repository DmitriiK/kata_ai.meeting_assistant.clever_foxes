
from llm_service import list_models, chat
from meeting_assistant_service import MeetingAssistantService
from summary_manager import MeetingSummaryManager


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


def test_meeting_assistant_initialization():
    """Test that MeetingAssistantService initializes correctly."""
    assistant = MeetingAssistantService()
    
    assert assistant.min_text_length == 50, "Expected default min_text_length to be 50"
    assert len(assistant.conversation_history) == 0, "Expected empty conversation history"
    assert len(assistant.key_points) == 0, "Expected empty key points"
    assert len(assistant.action_items) == 0, "Expected empty action items"
    assert len(assistant.decisions) == 0, "Expected empty decisions"
    assert len(assistant.suggested_questions) == 0, "Expected empty questions"
    assert not assistant.session_active, "Expected session to be inactive initially"
    
    print("✅ Meeting Assistant Service initialized correctly")


def test_meeting_assistant_short_transcription():
    """Test adding a short transcription that shouldn't trigger analysis."""
    assistant = MeetingAssistantService(min_text_length=20)
    
    result = assistant.add_transcription("Hi", "microphone", "2025-10-10 10:00:00")
    
    assert result == {}, "Expected empty result for short text"
    assert len(assistant.conversation_history) == 1, "Expected conversation history to have 1 item"
    assert assistant.session_active, "Expected session to be started"
    
    print("✅ Short transcription handled correctly")


def test_summary_manager_initialization():
    """Test that MeetingSummaryManager initializes correctly."""
    import tempfile
    temp_dir = tempfile.mkdtemp()
    
    manager = MeetingSummaryManager(output_dir=temp_dir)
    
    assert manager.base_output_dir.exists(), "Expected base output directory to exist"
    assert manager.current_session is None, "Expected no current session"
    assert manager.session_output_dir is None, "Expected no session output directory initially"
    assert len(manager.insights) == 0, "Expected empty insights"
    assert manager.total_transcripts == 0, "Expected zero transcripts"
    assert manager.total_insights == 0, "Expected zero insights"
    
    print("✅ Meeting Summary Manager initialized correctly")


def test_summary_manager_session():
    """Test starting and ending a meeting session."""
    import tempfile
    temp_dir = tempfile.mkdtemp()
    
    manager = MeetingSummaryManager(output_dir=temp_dir)
    
    # Start session
    session_id = manager.start_new_session("Test Meeting")
    assert manager.current_session is not None, "Expected active session"
    assert manager.current_session.session_id == session_id, "Expected session ID to match"
    assert manager.current_session.title == "Test Meeting", "Expected title to match"
    
    # Add some data
    manager.add_insight("question", "What's the timeline?", "AI Assistant")
    manager.add_transcript_count(5)
    
    assert len(manager.insights) == 1, "Expected 1 insight"
    assert manager.current_session.transcript_count == 5, "Expected 5 transcripts"
    
    # End session
    summary_file = manager.end_current_session()
    assert summary_file is not None, "Expected summary file path"
    assert manager.current_session is None, "Expected no active session"
    assert len(manager.insights) == 0, "Expected insights to be cleared"
    
    print("✅ Meeting session lifecycle works correctly")


def test_chat_meeting_question():
    """Test generating a meeting-related response."""
    message = "Based on our discussion about the new project, what are some good follow-up questions to ask?"
    response = chat(message, max_tokens=150)
    
    # Check that we got some response
    assert isinstance(response, str), "Expected response to be a string"
    assert len(response) > 0, "Expected non-empty response"
    assert not response.startswith("Error:"), f"Got error response: {response}"
    
    print(f"Meeting Question: {message}")
    print(f"AI Response: {response}")
    print("✅ Meeting-focused chat works correctly")


if __name__ == "__main__":
    # Run all tests
    print("🧪 Running Meeting Assistant Tests...")
    print("=" * 50)
    
    try:
        test_list_models()
        test_chat_hi()
        test_meeting_assistant_initialization()
        test_meeting_assistant_short_transcription()
        test_summary_manager_initialization()
        test_summary_manager_session()
        test_chat_meeting_question()
        
        print("=" * 50)
        print("✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise
