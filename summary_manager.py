"""
Meeting Summary Manager

Handles accumulation, organization, and persistence of meeting summaries,
key decisions, and action items throughout the meeting session.
"""
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class MeetingSession:
    """Data class for a meeting session."""
    session_id: str
    start_time: str
    end_time: Optional[str] = None
    title: str = "Meeting Session"
    participants: List[str] = None
    transcript_count: int = 0
    
    def __post_init__(self):
        if self.participants is None:
            self.participants = []


@dataclass
class MeetingInsight:
    """Data class for a meeting insight."""
    timestamp: str
    type: str  # 'question', 'key_point', 'action_item', 'decision'
    content: str
    source: str
    confidence: float = 1.0


class MeetingSummaryManager:
    """Manages meeting summaries and insights throughout sessions."""
    
    def __init__(self, output_dir: str = "sessions"):
        """
        Initialize the summary manager.
        
        Args:
            output_dir: Base directory to store session folders
        """
        self.base_output_dir = Path(output_dir)
        self.base_output_dir.mkdir(exist_ok=True)
        self.session_output_dir = None  # Will be set when session starts
        
        # Current session data
        self.current_session: Optional[MeetingSession] = None
        self.insights: List[MeetingInsight] = []
        
        # Statistics
        self.total_transcripts = 0
        self.total_insights = 0
        
    def start_new_session(self, title: str = None) -> str:
        """
        Start a new meeting session.
        
        Args:
            title: Optional meeting title
            
        Returns:
            Session ID
        """
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create session-specific output directory
        self.session_output_dir = self.base_output_dir / f"session_{session_id}"
        self.session_output_dir.mkdir(exist_ok=True)
        print(f"📁 Created session folder: {self.session_output_dir}")
        
        self.current_session = MeetingSession(
            session_id=session_id,
            start_time=start_time,
            title=title or f"Meeting Session {session_id}"
        )
        
        self.insights.clear()
        print(f"🟢 Started new meeting session: {self.current_session.title}")
        return session_id
    
    def end_current_session(self) -> Optional[str]:
        """
        End the current meeting session and save summary.
        
        Returns:
            Path to saved summary file, or None if no session active
        """
        if not self.current_session:
            print("⚠️  No active meeting session to end")
            return None
        
        self.current_session.end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Save final summary
        summary_file = self.save_session_summary()
        
        print(f"🔴 Ended meeting session: {self.current_session.title}")
        if summary_file:
            print(f"💾 Summary saved to: {summary_file}")
        
        # Reset for next session
        self.current_session = None
        self.insights.clear()
        
        return summary_file
    
    def add_insight(self, insight_type: str, content: str, source: str, confidence: float = 1.0):
        """
        Add a new insight to the current session.
        
        Args:
            insight_type: Type of insight ('question', 'key_point', 'action_item', 'decision')
            content: The insight content
            source: Source of the insight
            confidence: Confidence score (0.0 to 1.0)
        """
        if not self.current_session:
            print("⚠️  No active session. Starting new session...")
            self.start_new_session()
        
        insight = MeetingInsight(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            type=insight_type,
            content=content,
            source=source,
            confidence=confidence
        )
        
        self.insights.append(insight)
        self.total_insights += 1
    
    def add_transcript_count(self, count: int = 1):
        """Update transcript count for current session."""
        if self.current_session:
            self.current_session.transcript_count += count
        self.total_transcripts += count
    
    def get_insights_by_type(self, insight_type: str) -> List[MeetingInsight]:
        """Get all insights of a specific type."""
        return [insight for insight in self.insights if insight.type == insight_type]
    
    def get_recent_insights(self, minutes: int = 10) -> List[MeetingInsight]:
        """Get insights from the last N minutes."""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_insights = []
        
        for insight in self.insights:
            insight_time = datetime.strptime(insight.timestamp, "%Y-%m-%d %H:%M:%S")
            if insight_time >= cutoff_time:
                recent_insights.append(insight)
        
        return recent_insights
    
    def generate_session_summary(self) -> Dict[str, Any]:
        """Generate a comprehensive summary of the current session."""
        if not self.current_session:
            return {"error": "No active session"}
        
        # Categorize insights
        questions = self.get_insights_by_type('question')
        key_points = self.get_insights_by_type('key_point')
        action_items = self.get_insights_by_type('action_item')
        decisions = self.get_insights_by_type('decision')
        
        # Calculate session duration
        start_time = datetime.strptime(self.current_session.start_time, "%Y-%m-%d %H:%M:%S")
        if self.current_session.end_time:
            end_time = datetime.strptime(self.current_session.end_time, "%Y-%m-%d %H:%M:%S")
        else:
            end_time = datetime.now()
        
        duration_minutes = int((end_time - start_time).total_seconds() / 60)
        
        summary = {
            "session_info": asdict(self.current_session),
            "duration_minutes": duration_minutes,
            "statistics": {
                "total_transcripts": self.current_session.transcript_count,
                "total_insights": len(self.insights),
                "questions_generated": len(questions),
                "key_points_identified": len(key_points),
                "action_items_captured": len(action_items),
                "decisions_recorded": len(decisions)
            },
            "insights": {
                "questions": [{"content": q.content, "timestamp": q.timestamp, "source": q.source} for q in questions],
                "key_points": [{"content": kp.content, "timestamp": kp.timestamp, "source": kp.source} for kp in key_points],
                "action_items": [{"content": ai.content, "timestamp": ai.timestamp, "source": ai.source} for ai in action_items],
                "decisions": [{"content": d.content, "timestamp": d.timestamp, "source": d.source} for d in decisions]
            },
            "summary_generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return summary
    
    def save_session_summary(self, filename: str = None) -> Optional[str]:
        """
        Save the current session summary to a file.
        
        Args:
            filename: Optional custom filename
            
        Returns:
            Path to saved file, or None if failed
        """
        if not self.current_session or not self.session_output_dir:
            return None
        
        summary = self.generate_session_summary()
        
        if filename is None:
            filename = f"meeting_summary_{self.current_session.session_id}.json"
        
        filepath = self.session_output_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            return str(filepath)
            
        except Exception as e:
            print(f"❌ Error saving summary: {e}")
            return None
    
    def load_session_summary(self, filepath: str) -> Optional[Dict[str, Any]]:
        """Load a previously saved session summary."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading summary: {e}")
            return None
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """Get statistics for the current session."""
        if not self.current_session:
            return {"error": "No active session"}
        
        return {
            "session_id": self.current_session.session_id,
            "duration_minutes": self._get_session_duration_minutes(),
            "transcripts": self.current_session.transcript_count,
            "total_insights": len(self.insights),
            "questions": len(self.get_insights_by_type('question')),
            "key_points": len(self.get_insights_by_type('key_point')),
            "action_items": len(self.get_insights_by_type('action_item')),
            "decisions": len(self.get_insights_by_type('decision'))
        }
    
    def _get_session_duration_minutes(self) -> int:
        """Calculate session duration in minutes."""
        if not self.current_session:
            return 0
        
        start_time = datetime.strptime(self.current_session.start_time, "%Y-%m-%d %H:%M:%S")
        if self.current_session.end_time:
            end_time = datetime.strptime(self.current_session.end_time, "%Y-%m-%d %H:%M:%S")
        else:
            end_time = datetime.now()
        
        return int((end_time - start_time).total_seconds() / 60)
    
    def display_session_status(self):
        """Display current session status."""
        if not self.current_session:
            print("📊 No active meeting session")
            return
        
        stats = self.get_session_statistics()
        
        print(f"\n📊 SESSION STATUS")
        print("=" * 40)
        print(f"Session: {self.current_session.title}")
        print(f"Duration: {stats['duration_minutes']} minutes")
        print(f"Transcripts: {stats['transcripts']}")
        print(f"Total Insights: {stats['total_insights']}")
        print(f"  📝 Questions: {stats['questions']}")
        print(f"  🔑 Key Points: {stats['key_points']}")
        print(f"  📋 Action Items: {stats['action_items']}")
        print(f"  ✅ Decisions: {stats['decisions']}")
        print("=" * 40)
    
    def export_to_markdown(self, filepath: str = None) -> Optional[str]:
        """Export session summary to Markdown format."""
        if not self.current_session or not self.session_output_dir:
            return None
        
        summary = self.generate_session_summary()
        
        if filepath is None:
            filepath = self.session_output_dir / f"meeting_summary_{self.current_session.session_id}.md"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# {summary['session_info']['title']}\n\n")
                f.write(f"**Session ID:** {summary['session_info']['session_id']}\n")
                f.write(f"**Start Time:** {summary['session_info']['start_time']}\n")
                if summary['session_info']['end_time']:
                    f.write(f"**End Time:** {summary['session_info']['end_time']}\n")
                f.write(f"**Duration:** {summary['duration_minutes']} minutes\n\n")
                
                f.write("## Statistics\n\n")
                stats = summary['statistics']
                f.write(f"- Total Transcripts: {stats['total_transcripts']}\n")
                f.write(f"- Total Insights: {stats['total_insights']}\n")
                f.write(f"- Questions Generated: {stats['questions_generated']}\n")
                f.write(f"- Key Points Identified: {stats['key_points_identified']}\n")
                f.write(f"- Action Items Captured: {stats['action_items_captured']}\n")
                f.write(f"- Decisions Recorded: {stats['decisions_recorded']}\n\n")
                
                insights = summary['insights']
                
                if insights['key_points']:
                    f.write("## Key Points\n\n")
                    for i, point in enumerate(insights['key_points'], 1):
                        f.write(f"{i}. {point['content']}\n")
                    f.write("\n")
                
                if insights['decisions']:
                    f.write("## Decisions\n\n")
                    for i, decision in enumerate(insights['decisions'], 1):
                        f.write(f"{i}. {decision['content']}\n")
                    f.write("\n")
                
                if insights['action_items']:
                    f.write("## Action Items\n\n")
                    for i, item in enumerate(insights['action_items'], 1):
                        f.write(f"- [ ] {item['content']}\n")
                    f.write("\n")
                
                if insights['questions']:
                    f.write("## Suggested Follow-up Questions\n\n")
                    for i, question in enumerate(insights['questions'], 1):
                        f.write(f"{i}. {question['content']}\n")
                    f.write("\n")
            
            return str(filepath)
            
        except Exception as e:
            print(f"❌ Error exporting to Markdown: {e}")
            return None