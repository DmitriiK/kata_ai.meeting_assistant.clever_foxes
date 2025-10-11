"""
AI-Powered Meeting Assistant Service

Provides intelligent meeting assistance features:
- Suggests follow-up questions and prompts
- Summarizes key points and decisions
- Tracks action items and important topics
"""
import json
from typing import List, Dict, Optional, Any
from datetime import datetime
from llm_service import chat
from summary_manager import MeetingSummaryManager
from colorama import Fore, Back, Style, init

# Initialize colorama for cross-platform colored output
init(autoreset=True)


class MeetingAssistantService:
    """AI-powered meeting assistant that provides real-time insights."""
    
    def __init__(self, min_text_length: int = 50):
        """
        Initialize the meeting assistant.
        
        Args:
            min_text_length: Minimum text length to trigger analysis
        """
        self.min_text_length = min_text_length
        self.conversation_history: List[Dict[str, Any]] = []
        self.key_points: List[str] = []
        self.action_items: List[str] = []
        self.decisions: List[str] = []
        self.suggested_questions: List[str] = []
        
        # Context window management
        self.max_history_items = 10
        
        # Initialize summary manager
        self.summary_manager = MeetingSummaryManager()
        self.session_active = False
        
    def add_transcription(self, text: str, source: str, timestamp: str) -> Dict[str, Any]:
        """
        Add new transcription and trigger AI analysis.
        
        Args:
            text: Transcribed text
            source: Audio source (microphone/system)
            timestamp: When the text was transcribed
            
        Returns:
            Dict containing AI insights
        """
        # Start session if not already active
        if not self.session_active:
            self.start_session()
        
        # Add to conversation history
        self.conversation_history.append({
            "text": text,
            "source": source,
            "timestamp": timestamp
        })
        
        # Update transcript count in summary manager
        self.summary_manager.add_transcript_count(1)
        
        # Keep only recent history to manage context window
        if len(self.conversation_history) > self.max_history_items:
            self.conversation_history = self.conversation_history[-self.max_history_items:]
        
        # Trigger analysis if text is substantial enough
        if len(text.strip()) >= self.min_text_length:
            return self.analyze_conversation()
        
        return {}
    
    def analyze_conversation(self) -> Dict[str, Any]:
        """
        Analyze the recent conversation and generate insights.
        
        Returns:
            Dict containing analysis results
        """
        if not self.conversation_history:
            return {}
        
        # Get recent conversation context
        recent_text = self._get_recent_context()
        
        # Generate different types of insights
        insights = {}
        
        try:
            # Generate follow-up questions
            questions = self._generate_follow_up_questions(recent_text)
            if questions:
                insights["questions"] = questions
                self.suggested_questions.extend(questions)
                # Add to summary manager
                for question in questions:
                    self.summary_manager.add_insight('question', question, 'AI Assistant')
            
            # Extract key points
            key_points = self._extract_key_points(recent_text)
            if key_points:
                insights["key_points"] = key_points
                self.key_points.extend(key_points)
                # Add to summary manager
                for point in key_points:
                    self.summary_manager.add_insight('key_point', point, 'AI Assistant')
            
            # Identify action items
            actions = self._identify_action_items(recent_text)
            if actions:
                insights["action_items"] = actions
                self.action_items.extend(actions)
                # Add to summary manager
                for action in actions:
                    self.summary_manager.add_insight('action_item', action, 'AI Assistant')
            
            # Identify decisions
            decisions = self._identify_decisions(recent_text)
            if decisions:
                insights["decisions"] = decisions
                self.decisions.extend(decisions)
                # Add to summary manager
                for decision in decisions:
                    self.summary_manager.add_insight('decision', decision, 'AI Assistant')
                
        except Exception as e:
            print(f"❌ Error during AI analysis: {e}")
            insights["error"] = str(e)
        
        return insights
    
    def _get_recent_context(self, max_chars: int = 2000) -> str:
        """
        Get recent conversation context for AI analysis.
        
        Args:
            max_chars: Maximum characters to include
            
        Returns:
            Recent conversation text
        """
        if not self.conversation_history:
            return ""
        
        # Combine recent conversation
        context_parts = []
        char_count = 0
        
        for entry in reversed(self.conversation_history):
            text = f"[{entry['source']}] {entry['text']}"
            if char_count + len(text) > max_chars:
                break
            context_parts.insert(0, text)
            char_count += len(text)
        
        return "\n".join(context_parts)
    
    def _generate_follow_up_questions(self, context: str) -> List[str]:
        """Generate relevant follow-up questions based on conversation."""
        prompt = f"""
Based on this meeting conversation, suggest 2-3 relevant follow-up questions that would help clarify or expand on the topics being discussed:

CONVERSATION:
{context}

Please provide 2-3 specific, actionable follow-up questions that would be helpful to ask. Format as a simple list, one question per line, without numbering or bullet points.
"""
        
        try:
            response = chat(prompt)
            if response and not response.startswith("Error:"):
                # Parse questions from response
                questions = [q.strip() for q in response.split('\n') if q.strip() and not q.startswith('Error')]
                return questions[:3]  # Limit to 3 questions
        except Exception as e:
            print(f"Error generating questions: {e}")
        
        return []
    
    def _extract_key_points(self, context: str) -> List[str]:
        """Extract key points and important information from conversation."""
        prompt = f"""
Analyze this meeting conversation and extract the most important key points or topics being discussed:

CONVERSATION:
{context}

Please provide 1-3 key points or important topics. Format as a simple list, one point per line, without numbering or bullet points. Keep each point concise (1-2 sentences max).
"""
        
        try:
            response = chat(prompt)
            if response and not response.startswith("Error:"):
                # Parse key points from response
                points = [point.strip() for point in response.split('\n') if point.strip() and not point.startswith('Error')]
                return points[:3]  # Limit to 3 points
        except Exception as e:
            print(f"Error extracting key points: {e}")
        
        return []
    
    def _identify_action_items(self, context: str) -> List[str]:
        """Identify action items and tasks mentioned in conversation."""
        prompt = f"""
Analyze this meeting conversation and identify any action items, tasks, or commitments mentioned:

CONVERSATION:
{context}

Please identify any action items, tasks, or commitments. Format as a simple list, one item per line, without numbering or bullet points. Only include clear, actionable items.
"""
        
        try:
            response = chat(prompt)
            if response and not response.startswith("Error:"):
                # Parse action items from response
                items = [item.strip() for item in response.split('\n') if item.strip() and not item.startswith('Error')]
                return items[:3]  # Limit to 3 items
        except Exception as e:
            print(f"Error identifying action items: {e}")
        
        return []
    
    def _identify_decisions(self, context: str) -> List[str]:
        """Identify decisions or conclusions made in conversation."""
        prompt = f"""
Analyze this meeting conversation and identify any decisions, conclusions, or agreements made:

CONVERSATION:
{context}

Please identify any clear decisions, conclusions, or agreements. Format as a simple list, one decision per line, without numbering or bullet points. Only include definitive decisions.
"""
        
        try:
            response = chat(prompt)
            if response and not response.startswith("Error:"):
                # Parse decisions from response
                decisions = [decision.strip() for decision in response.split('\n') if decision.strip() and not decision.startswith('Error')]
                return decisions[:3]  # Limit to 3 decisions
        except Exception as e:
            print(f"Error identifying decisions: {e}")
        
        return []
    
    def get_meeting_summary(self) -> Dict[str, Any]:
        """
        Generate a comprehensive meeting summary.
        
        Returns:
            Dict containing meeting summary
        """
        # Generate overall summary
        context = self._get_recent_context(max_chars=3000)
        
        summary_prompt = f"""
Based on this entire meeting conversation, provide a comprehensive summary:

CONVERSATION:
{context}

Please provide:
1. A brief overall summary (2-3 sentences)
2. Main topics discussed
3. Key outcomes or conclusions

Format your response clearly with headers.
"""
        
        try:
            summary_text = chat(summary_prompt)
            
            summary = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "overall_summary": summary_text,
                "key_points": list(set(self.key_points)),  # Remove duplicates
                "action_items": list(set(self.action_items)),
                "decisions": list(set(self.decisions)),
                "suggested_questions": list(set(self.suggested_questions)),
                "conversation_count": len(self.conversation_history)
            }
            
            return summary
            
        except Exception as e:
            print(f"Error generating meeting summary: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def display_insights(self, insights: Dict[str, Any]):
        """Display AI insights in a formatted way and save them to files."""
        if not insights:
            return
        
        print(f"\n{Back.MAGENTA}{Fore.WHITE}🤖 AI MEETING ASSISTANT{Style.RESET_ALL}")
        print("=" * 50)
        
        if "questions" in insights:
            print(f"\n{Fore.CYAN}❓ SUGGESTED FOLLOW-UP QUESTIONS:{Style.RESET_ALL}")
            for i, question in enumerate(insights["questions"], 1):
                print(f"   {i}. {question}")
        
        if "key_points" in insights:
            print(f"\n{Fore.GREEN}🔑 KEY POINTS:{Style.RESET_ALL}")
            for point in insights["key_points"]:
                print(f"   • {point}")
        
        if "action_items" in insights:
            print(f"\n{Fore.YELLOW}📋 ACTION ITEMS:{Style.RESET_ALL}")
            for item in insights["action_items"]:
                print(f"   • {item}")
        
        if "decisions" in insights:
            print(f"\n{Fore.RED}✅ DECISIONS:{Style.RESET_ALL}")
            for decision in insights["decisions"]:
                print(f"   • {decision}")
        
        if "error" in insights:
            print(f"\n{Fore.RED}❌ Error: {insights['error']}{Style.RESET_ALL}")
        
        print("=" * 50)
        
        # Save insights to individual files if session is active
        self._save_real_time_insights(insights)
    
    def _save_real_time_insights(self, insights: Dict[str, Any]):
        """Save real-time insights to individual files in the session folder."""
        if not insights or not self.session_active or not self.summary_manager.session_output_dir:
            return
        
        session_dir = self.summary_manager.session_output_dir
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            # Save follow-up questions
            if "questions" in insights and insights["questions"]:
                questions_file = session_dir / "follow-up-questions.txt"
                with open(questions_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n=== {timestamp} ===\n")
                    for i, question in enumerate(insights["questions"], 1):
                        f.write(f"{i}. {question}\n")
                    f.write("\n")
            
            # Save key points
            if "key_points" in insights and insights["key_points"]:
                key_points_file = session_dir / "key-points.txt"
                with open(key_points_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n=== {timestamp} ===\n")
                    for point in insights["key_points"]:
                        f.write(f"• {point}\n")
                    f.write("\n")
            
            # Save action items
            if "action_items" in insights and insights["action_items"]:
                action_items_file = session_dir / "action-items.txt"
                with open(action_items_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n=== {timestamp} ===\n")
                    for item in insights["action_items"]:
                        f.write(f"• {item}\n")
                    f.write("\n")
            
            # Save decisions
            if "decisions" in insights and insights["decisions"]:
                decisions_file = session_dir / "decisions.txt"
                with open(decisions_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n=== {timestamp} ===\n")
                    for decision in insights["decisions"]:
                        f.write(f"• {decision}\n")
                    f.write("\n")
                        
        except Exception as e:
            print(f"⚠️  Warning: Could not save real-time insights to files: {e}")
    
    def save_summary_to_file(self, filename: str = None):
        """Save meeting summary to file."""
        if self.session_active:
            # Use summary manager for active session
            return self.summary_manager.save_session_summary(filename)
        else:
            # Fallback to legacy method for backward compatibility
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"meeting_summary_{timestamp}.json"
            
            summary = self.get_meeting_summary()
            
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(summary, f, indent=2, ensure_ascii=False)
                
                print(f"💾 Meeting summary saved to: {filename}")
                return filename
                
            except Exception as e:
                print(f"❌ Error saving summary: {e}")
                return None
    
    def start_session(self, title: str = None):
        """Start a new meeting session."""
        if self.session_active:
            print("⚠️  Session already active. Ending current session first...")
            self.end_session()
        
        session_id = self.summary_manager.start_new_session(title)
        self.session_active = True
        print(f"🟢 Meeting session started: {session_id}")
        return session_id
    
    def end_session(self) -> Optional[str]:
        """End the current meeting session and save summary."""
        if not self.session_active:
            print("⚠️  No active session to end")
            return None
        
        # Generate final comprehensive summary
        print("📋 Generating comprehensive meeting summary...")
        summary_file = self.summary_manager.end_current_session()
        
        # Also export to Markdown
        if summary_file:
            md_file = self.summary_manager.export_to_markdown()
            if md_file:
                print(f"📄 Markdown summary: {md_file}")
        
        self.session_active = False
        
        # Reset local data
        self.conversation_history.clear()
        self.key_points.clear()
        self.action_items.clear()
        self.decisions.clear()
        self.suggested_questions.clear()
        
        return summary_file
    
    def get_session_status(self):
        """Display current session status."""
        self.summary_manager.display_session_status()
    
    def reset_session(self):
        """Reset the meeting session data."""
        if self.session_active:
            self.end_session()
        
        self.conversation_history.clear()
        self.key_points.clear()
        self.action_items.clear()
        self.decisions.clear()
        self.suggested_questions.clear()
        print("🔄 Meeting session reset")