"""
Tests for the Meeting Assistant Service
"""
import pytest
from unittest.mock import Mock, patch
from meeting_assistant_service import MeetingAssistantService
from summary_manager import MeetingSummaryManager, MeetingSession, MeetingInsight
import tempfile
import json
import os


class TestMeetingAssistantService:
    """Test cases for MeetingAssistantService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.assistant = MeetingAssistantService(min_text_length=10)
    
    def test_initialization(self):
        """Test that the service initializes correctly."""
        assert self.assistant.min_text_length == 10
        assert len(self.assistant.conversation_history) == 0
        assert len(self.assistant.key_points) == 0
        assert len(self.assistant.action_items) == 0
        assert len(self.assistant.decisions) == 0
        assert len(self.assistant.suggested_questions) == 0
        assert not self.assistant.session_active
        assert isinstance(self.assistant.summary_manager, MeetingSummaryManager)
    
    def test_add_transcription_short_text(self):
        """Test adding transcription with text too short to trigger analysis."""
        result = self.assistant.add_transcription("Hi", "microphone", "2025-10-10 10:00:00")
        
        assert result == {}
        assert len(self.assistant.conversation_history) == 1
        assert self.assistant.session_active  # Session should be started
    
    @patch('meeting_assistant_service.chat')
    def test_add_transcription_long_text(self, mock_chat):
        """Test adding transcription with text long enough to trigger analysis."""
        mock_chat.return_value = "What are the next steps for this project?"
        
        long_text = "This is a long enough text to trigger AI analysis in our meeting"
        result = self.assistant.add_transcription(long_text, "microphone", "2025-10-10 10:00:00")
        
        assert len(self.assistant.conversation_history) == 1
        assert self.assistant.session_active
        # Should have called chat function for analysis
        assert mock_chat.called
    
    def test_get_recent_context(self):
        """Test getting recent conversation context."""
        # Add some conversation history
        self.assistant.conversation_history = [
            {"text": "Hello everyone", "source": "mic", "timestamp": "10:00:00"},
            {"text": "Let's discuss the project", "source": "mic", "timestamp": "10:01:00"}
        ]
        
        context = self.assistant._get_recent_context()
        assert "Hello everyone" in context
        assert "Let's discuss the project" in context
    
    @patch('meeting_assistant_service.chat')
    def test_generate_follow_up_questions(self, mock_chat):
        """Test generating follow-up questions."""
        mock_chat.return_value = "What are the success criteria?\nWho will be responsible for implementation?"
        
        questions = self.assistant._generate_follow_up_questions("We need to start the new project")
        
        assert len(questions) == 2
        assert "What are the success criteria?" in questions
        assert "Who will be responsible for implementation?" in questions
    
    @patch('meeting_assistant_service.chat')
    def test_extract_key_points(self, mock_chat):
        """Test extracting key points from conversation."""
        mock_chat.return_value = "New project initiation\nTeam restructuring needed"
        
        key_points = self.assistant._extract_key_points("We're starting a new project and need to restructure the team")
        
        assert len(key_points) == 2
        assert "New project initiation" in key_points
        assert "Team restructuring needed" in key_points
    
    @patch('meeting_assistant_service.chat')
    def test_identify_action_items(self, mock_chat):
        """Test identifying action items."""
        mock_chat.return_value = "John will create the project plan\nMaria will set up the team meetings"
        
        actions = self.assistant._identify_action_items("John, please create the project plan. Maria, can you set up weekly team meetings?")
        
        assert len(actions) == 2
        assert "John will create the project plan" in actions
        assert "Maria will set up the team meetings" in actions
    
    @patch('meeting_assistant_service.chat')
    def test_identify_decisions(self, mock_chat):
        """Test identifying decisions made in conversation."""
        mock_chat.return_value = "Use React for frontend development\nMeet every Tuesday at 2 PM"
        
        decisions = self.assistant._identify_decisions("We decided to use React for the frontend and meet every Tuesday at 2 PM")
        
        assert len(decisions) == 2
        assert "Use React for frontend development" in decisions
        assert "Meet every Tuesday at 2 PM" in decisions
    
    def test_session_management(self):
        """Test starting and ending sessions."""
        # Start session
        session_id = self.assistant.start_session("Test Meeting")
        assert self.assistant.session_active
        assert session_id is not None
        
        # End session
        with patch.object(self.assistant.summary_manager, 'end_current_session') as mock_end:
            mock_end.return_value = "test_summary.json"
            result = self.assistant.end_session()
            assert result == "test_summary.json"
            assert not self.assistant.session_active
    
    def test_display_insights(self, capsys):
        """Test displaying insights output."""
        insights = {
            "questions": ["What's the timeline?", "Who's responsible?"],
            "key_points": ["Budget approved", "Team expanded"],
            "action_items": ["Create timeline", "Hire developers"],
            "decisions": ["Use cloud hosting", "Meet weekly"]
        }
        
        self.assistant.display_insights(insights)
        captured = capsys.readouterr()
        
        assert "AI MEETING ASSISTANT" in captured.out
        assert "What's the timeline?" in captured.out
        assert "Budget approved" in captured.out
        assert "Create timeline" in captured.out
        assert "Use cloud hosting" in captured.out


class TestMeetingSummaryManager:
    """Test cases for MeetingSummaryManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Use temporary directory for tests
        self.temp_dir = tempfile.mkdtemp()
        self.manager = MeetingSummaryManager(output_dir=self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test that the manager initializes correctly."""
        assert self.manager.output_dir.exists()
        assert self.manager.current_session is None
        assert len(self.manager.insights) == 0
        assert self.manager.total_transcripts == 0
        assert self.manager.total_insights == 0
    
    def test_start_new_session(self):
        """Test starting a new meeting session."""
        session_id = self.manager.start_new_session("Test Meeting")
        
        assert self.manager.current_session is not None
        assert self.manager.current_session.session_id == session_id
        assert self.manager.current_session.title == "Test Meeting"
        assert self.manager.current_session.start_time is not None
        assert self.manager.current_session.end_time is None
    
    def test_add_insight(self):
        """Test adding insights to the session."""
        self.manager.start_new_session("Test Meeting")
        
        self.manager.add_insight("question", "What's the budget?", "AI Assistant")
        self.manager.add_insight("key_point", "Project approved", "AI Assistant")
        
        assert len(self.manager.insights) == 2
        assert self.manager.insights[0].type == "question"
        assert self.manager.insights[0].content == "What's the budget?"
        assert self.manager.insights[1].type == "key_point"
        assert self.manager.insights[1].content == "Project approved"
    
    def test_get_insights_by_type(self):
        """Test filtering insights by type."""
        self.manager.start_new_session("Test Meeting")
        
        self.manager.add_insight("question", "What's the timeline?", "AI Assistant")
        self.manager.add_insight("key_point", "Budget approved", "AI Assistant")
        self.manager.add_insight("question", "Who's responsible?", "AI Assistant")
        
        questions = self.manager.get_insights_by_type("question")
        key_points = self.manager.get_insights_by_type("key_point")
        
        assert len(questions) == 2
        assert len(key_points) == 1
        assert all(insight.type == "question" for insight in questions)
        assert all(insight.type == "key_point" for insight in key_points)
    
    def test_add_transcript_count(self):
        """Test updating transcript count."""
        self.manager.start_new_session("Test Meeting")
        
        self.manager.add_transcript_count(5)
        assert self.manager.current_session.transcript_count == 5
        assert self.manager.total_transcripts == 5
        
        self.manager.add_transcript_count(3)
        assert self.manager.current_session.transcript_count == 8
        assert self.manager.total_transcripts == 8
    
    def test_generate_session_summary(self):
        """Test generating a comprehensive session summary."""
        self.manager.start_new_session("Test Meeting")
        
        # Add some test data
        self.manager.add_insight("question", "What's the budget?", "AI Assistant")
        self.manager.add_insight("key_point", "Project approved", "AI Assistant")
        self.manager.add_insight("action_item", "Create project plan", "AI Assistant")
        self.manager.add_insight("decision", "Use React framework", "AI Assistant")
        self.manager.add_transcript_count(10)
        
        summary = self.manager.generate_session_summary()
        
        assert "session_info" in summary
        assert "statistics" in summary
        assert "insights" in summary
        assert summary["statistics"]["total_transcripts"] == 10
        assert summary["statistics"]["questions_generated"] == 1
        assert summary["statistics"]["key_points_identified"] == 1
        assert summary["statistics"]["action_items_captured"] == 1
        assert summary["statistics"]["decisions_recorded"] == 1
    
    def test_save_session_summary(self):
        """Test saving session summary to file."""
        self.manager.start_new_session("Test Meeting")
        self.manager.add_insight("key_point", "Test point", "AI Assistant")
        
        filepath = self.manager.save_session_summary()
        
        assert filepath is not None
        assert os.path.exists(filepath)
        
        # Load and verify the saved file
        with open(filepath, 'r', encoding='utf-8') as f:
            saved_summary = json.load(f)
        
        assert "session_info" in saved_summary
        assert "insights" in saved_summary
        assert len(saved_summary["insights"]["key_points"]) == 1
    
    def test_export_to_markdown(self):
        """Test exporting session summary to Markdown."""
        self.manager.start_new_session("Test Meeting")
        self.manager.add_insight("key_point", "Important decision made", "AI Assistant")
        self.manager.add_insight("action_item", "Follow up with client", "AI Assistant")
        
        md_filepath = self.manager.export_to_markdown()
        
        assert md_filepath is not None
        assert os.path.exists(md_filepath)
        assert md_filepath.endswith('.md')
        
        # Read and verify Markdown content
        with open(md_filepath, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        assert "# Test Meeting" in md_content
        assert "## Key Points" in md_content
        assert "## Action Items" in md_content
        assert "Important decision made" in md_content
        assert "Follow up with client" in md_content
    
    def test_end_session(self):
        """Test ending a session."""
        self.manager.start_new_session("Test Meeting")
        self.manager.add_insight("key_point", "Test point", "AI Assistant")
        
        summary_file = self.manager.end_current_session()
        
        assert summary_file is not None
        assert os.path.exists(summary_file)
        assert self.manager.current_session is None
        assert len(self.manager.insights) == 0
    
    def test_get_session_statistics(self):
        """Test getting session statistics."""
        self.manager.start_new_session("Test Meeting")
        self.manager.add_insight("question", "Test question", "AI Assistant")
        self.manager.add_insight("key_point", "Test point", "AI Assistant")
        self.manager.add_transcript_count(5)
        
        stats = self.manager.get_session_statistics()
        
        assert "session_id" in stats
        assert "duration_minutes" in stats
        assert stats["transcripts"] == 5
        assert stats["total_insights"] == 2
        assert stats["questions"] == 1
        assert stats["key_points"] == 1


class TestMeetingInsight:
    """Test cases for MeetingInsight data class."""
    
    def test_meeting_insight_creation(self):
        """Test creating a MeetingInsight instance."""
        insight = MeetingInsight(
            timestamp="2025-10-10 10:00:00",
            type="question",
            content="What's the timeline?",
            source="AI Assistant",
            confidence=0.9
        )
        
        assert insight.timestamp == "2025-10-10 10:00:00"
        assert insight.type == "question"
        assert insight.content == "What's the timeline?"
        assert insight.source == "AI Assistant"
        assert insight.confidence == 0.9


class TestMeetingSession:
    """Test cases for MeetingSession data class."""
    
    def test_meeting_session_creation(self):
        """Test creating a MeetingSession instance."""
        session = MeetingSession(
            session_id="20251010_100000",
            start_time="2025-10-10 10:00:00",
            title="Test Meeting"
        )
        
        assert session.session_id == "20251010_100000"
        assert session.start_time == "2025-10-10 10:00:00"
        assert session.title == "Test Meeting"
        assert session.end_time is None
        assert session.participants == []
        assert session.transcript_count == 0
    
    def test_meeting_session_with_participants(self):
        """Test creating a MeetingSession with participants."""
        participants = ["Alice", "Bob", "Charlie"]
        session = MeetingSession(
            session_id="20251010_100000",
            start_time="2025-10-10 10:00:00",
            title="Team Meeting",
            participants=participants
        )
        
        assert session.participants == participants


if __name__ == "__main__":
    pytest.main([__file__])