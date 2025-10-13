"""
AI-Powered Meeting Assistant Service

Provides intelligent meeting assistance features:
- Suggests follow-up questions and prompts
- Summarizes key points and decisions
- Tracks action items and important topics
"""
import json
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from llm_service import chat
from summary_manager import MeetingSummaryManager
from colorama import Fore, Back, Style, init

# Initialize colorama for cross-platform colored output
init(autoreset=True)


class MeetingAssistantService:
    """AI-powered meeting assistant that provides real-time insights."""
    
    def __init__(self, 
                 min_text_length: int = 50,
                 min_analysis_interval: int = 45,
                 min_conversation_exchanges: int = 3,
                 similarity_threshold: float = 0.75):
        """
        Initialize the meeting assistant.
        
        Args:
            min_text_length: Minimum text length to trigger analysis
            min_analysis_interval: Minimum seconds between analyses (default: 45)
            min_conversation_exchanges: Minimum conversation exchanges before analysis
            similarity_threshold: Similarity threshold for duplicate detection (0.0-1.0)
        """
        self.min_text_length = min_text_length
        self.min_analysis_interval = min_analysis_interval
        self.min_conversation_exchanges = min_conversation_exchanges
        self.similarity_threshold = similarity_threshold
        
        self.conversation_history: List[Dict[str, Any]] = []
        self.key_points: List[str] = []
        self.action_items: List[str] = []
        self.decisions: List[str] = []
        self.suggested_questions: List[str] = []
        
        # Context window management (increased from 10)
        self.max_history_items = 20
        
        # Rate limiting
        self.last_analysis_time: Optional[datetime] = None
        self.conversation_count_since_analysis = 0
        
        # Accumulated context for batch analysis
        self.accumulated_chars = 0
        
        # Initialize summary manager
        self.summary_manager = MeetingSummaryManager()
        self.session_active = False
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two text strings.
        
        Args:
            text1: First text string
            text2: Second text string
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Normalize texts for comparison
        t1 = text1.lower().strip()
        t2 = text2.lower().strip()
        
        # Use SequenceMatcher for similarity calculation
        return SequenceMatcher(None, t1, t2).ratio()
    
    def _is_duplicate(self, new_text: str, existing_list: List[str]) -> bool:
        """
        Check if new text is a duplicate of any existing item.
        
        Args:
            new_text: New text to check
            existing_list: List of existing texts
            
        Returns:
            True if duplicate found, False otherwise
        """
        for existing_text in existing_list:
            similarity = self._calculate_similarity(new_text, existing_text)
            if similarity >= self.similarity_threshold:
                return True
        return False
    
    def _should_trigger_analysis(self) -> Tuple[bool, str]:
        """
        Determine if AI analysis should be triggered based on rate limiting
        and accumulated context.
        
        Returns:
            Tuple of (should_analyze, reason)
        """
        # Check if we have enough conversation exchanges
        if self.conversation_count_since_analysis < self.min_conversation_exchanges:
            return False, f"Only {self.conversation_count_since_analysis} exchanges (need {self.min_conversation_exchanges})"
        
        # Check rate limiting
        if self.last_analysis_time is not None:
            time_since_last = (datetime.now() - self.last_analysis_time).total_seconds()
            if time_since_last < self.min_analysis_interval:
                remaining = int(self.min_analysis_interval - time_since_last)
                return False, f"Rate limited (wait {remaining}s)"
        
        return True, "Ready for analysis"
        
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
        
        # Update counters
        self.conversation_count_since_analysis += 1
        self.accumulated_chars += len(text)
        
        # Update transcript count in summary manager
        self.summary_manager.add_transcript_count(1)
        
        # Keep only recent history to manage context window
        if len(self.conversation_history) > self.max_history_items:
            self.conversation_history = self.conversation_history[-self.max_history_items:]
        
        # Check if we should trigger analysis
        should_analyze, reason = self._should_trigger_analysis()
        
        if should_analyze and len(text.strip()) >= self.min_text_length:
            insights = self.analyze_conversation()
            # Reset counters after analysis
            self.conversation_count_since_analysis = 0
            self.accumulated_chars = 0
            self.last_analysis_time = datetime.now()
            return insights
        
        return {}
    
    def analyze_conversation(self) -> Dict[str, Any]:
        """
        Analyze the recent conversation and generate insights using a single consolidated LLM call.
        
        Returns:
            Dict containing analysis results
        """
        if not self.conversation_history:
            return {}
        
        # Get recent conversation context
        recent_text = self._get_recent_context(max_chars=4000)  # Increased from 2000
        
        # Generate insights with session-aware context
        insights = {}
        
        try:
            # Single consolidated LLM call for all insight types
            all_insights = self._generate_all_insights(recent_text)
            
            # Process and deduplicate each insight type
            if all_insights.get("questions"):
                new_questions = self._filter_duplicates(
                    all_insights["questions"], 
                    self.suggested_questions
                )
                if new_questions:
                    insights["questions"] = new_questions
                    self.suggested_questions.extend(new_questions)
                    # Add to summary manager
                    for question in new_questions:
                        self.summary_manager.add_insight('question', question, 'AI Assistant')
            
            if all_insights.get("key_points"):
                new_key_points = self._filter_duplicates(
                    all_insights["key_points"], 
                    self.key_points
                )
                if new_key_points:
                    insights["key_points"] = new_key_points
                    self.key_points.extend(new_key_points)
                    # Add to summary manager
                    for point in new_key_points:
                        self.summary_manager.add_insight('key_point', point, 'AI Assistant')
            
            if all_insights.get("action_items"):
                new_actions = self._filter_duplicates(
                    all_insights["action_items"], 
                    self.action_items
                )
                if new_actions:
                    insights["action_items"] = new_actions
                    self.action_items.extend(new_actions)
                    # Add to summary manager
                    for action in new_actions:
                        self.summary_manager.add_insight('action_item', action, 'AI Assistant')
            
            if all_insights.get("decisions"):
                new_decisions = self._filter_duplicates(
                    all_insights["decisions"], 
                    self.decisions
                )
                if new_decisions:
                    insights["decisions"] = new_decisions
                    self.decisions.extend(new_decisions)
                    # Add to summary manager
                    for decision in new_decisions:
                        self.summary_manager.add_insight('decision', decision, 'AI Assistant')
                
        except Exception as e:
            print(f"❌ Error during AI analysis: {e}")
            insights["error"] = str(e)
        
        return insights
    
    def _filter_duplicates(self, new_items: List[str], existing_items: List[str]) -> List[str]:
        """
        Filter out duplicate items based on similarity threshold.
        
        Args:
            new_items: List of new items to check
            existing_items: List of existing items
            
        Returns:
            List of non-duplicate items
        """
        filtered = []
        for item in new_items:
            if not self._is_duplicate(item, existing_items) and not self._is_duplicate(item, filtered):
                filtered.append(item)
        return filtered
    
    def _get_recent_context(self, max_chars: int = 4000) -> str:
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
    
    def _format_existing_insights(self) -> str:
        """
        Format existing insights for context in prompt.
        
        Returns:
            Formatted string of existing insights
        """
        context_parts = []
        
        # Show recent insights (last 5 of each type) to avoid repetition
        if self.key_points:
            recent_points = self.key_points[-5:]
            context_parts.append("ALREADY CAPTURED KEY POINTS:")
            for point in recent_points:
                context_parts.append(f"- {point}")
        
        if self.decisions:
            recent_decisions = self.decisions[-5:]
            context_parts.append("\nALREADY CAPTURED DECISIONS:")
            for decision in recent_decisions:
                context_parts.append(f"- {decision}")
        
        if self.action_items:
            recent_actions = self.action_items[-5:]
            context_parts.append("\nALREADY CAPTURED ACTION ITEMS:")
            for action in recent_actions:
                context_parts.append(f"- {action}")
        
        if self.suggested_questions:
            recent_questions = self.suggested_questions[-5:]
            context_parts.append("\nALREADY ASKED QUESTIONS:")
            for question in recent_questions:
                context_parts.append(f"- {question}")
        
        return "\n".join(context_parts) if context_parts else "No insights captured yet."
    
    def _generate_all_insights(self, context: str) -> Dict[str, List[str]]:
        """
        Generate all insight types in a single consolidated LLM call.
        
        Args:
            context: Recent conversation context
            
        Returns:
            Dict containing lists of questions, key_points, action_items, and decisions
        """
        existing_context = self._format_existing_insights()
        
        prompt = f"""You are an AI meeting assistant analyzing a conversation to extract insights.

IMPORTANT INSTRUCTIONS:
1. DO NOT repeat or rephrase insights that are already captured (see below)
2. Only identify NEW information not already documented
3. Be specific and actionable
4. If nothing new to add for a category, return an empty list for that category
5. Return your response as valid JSON only, no other text

{existing_context}

RECENT CONVERSATION:
{context}

Analyze the RECENT CONVERSATION above and extract:
1. Follow-up questions (2-3 max): Specific questions to clarify or expand on NEW topics
2. Key points (1-3 max): Important NEW information or topics discussed
3. Action items (0-3 max): Clear NEW tasks, commitments, or to-dos mentioned
4. Decisions (0-2 max): Definitive NEW decisions, conclusions, or agreements made

Return ONLY a JSON object in this exact format (with empty arrays if nothing new):
{{
  "questions": ["question 1", "question 2"],
  "key_points": ["point 1", "point 2"],
  "action_items": ["action 1", "action 2"],
  "decisions": ["decision 1"]
}}"""
        
        try:
            response = chat(prompt, max_tokens=800, temperature=0.7)
            
            # Try to parse JSON response
            if response and not response.startswith("Error:"):
                # Clean the response - sometimes LLMs add markdown code blocks
                clean_response = response.strip()
                if clean_response.startswith("```json"):
                    clean_response = clean_response[7:]
                if clean_response.startswith("```"):
                    clean_response = clean_response[3:]
                if clean_response.endswith("```"):
                    clean_response = clean_response[:-3]
                clean_response = clean_response.strip()
                
                try:
                    insights = json.loads(clean_response)
                    
                    # Validate structure and limit items
                    result = {
                        "questions": insights.get("questions", [])[:3],
                        "key_points": insights.get("key_points", [])[:3],
                        "action_items": insights.get("action_items", [])[:3],
                        "decisions": insights.get("decisions", [])[:2]
                    }
                    
                    # Filter out empty strings
                    result = {
                        k: [item.strip() for item in v if item and item.strip()]
                        for k, v in result.items()
                    }
                    
                    return result
                    
                except json.JSONDecodeError as e:
                    print(f"⚠️  Failed to parse LLM response as JSON: {e}")
                    print(f"Response was: {clean_response[:200]}")
                    return {"questions": [], "key_points": [], "action_items": [], "decisions": []}
        
        except Exception as e:
            print(f"Error generating insights: {e}")
        
        return {"questions": [], "key_points": [], "action_items": [], "decisions": []}
    
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