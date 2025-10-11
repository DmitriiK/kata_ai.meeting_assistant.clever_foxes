#!/usr/bin/env python3
"""
AI Meeting Assistant Demo

Demonstrates the capabilities of the meeting assistant without requiring 
actual audio input. Uses simulated meeting conversation data.
"""
import time
from meeting_assistant_service import MeetingAssistantService
from datetime import datetime


def simulate_meeting_conversation():
    """Simulate a meeting conversation to demonstrate AI capabilities."""
    
    print("🚀 AI Meeting Assistant Demo")
    print("=" * 60)
    print("This demo simulates a meeting conversation to show AI capabilities")
    print("=" * 60)
    
    # Initialize the meeting assistant
    assistant = MeetingAssistantService(min_text_length=20)
    
    # Simulated meeting conversation
    conversation_parts = [
        {
            "text": "Good morning everyone. Let's start today's project planning meeting. We need to discuss the new mobile app development timeline.",
            "source": "🎤 MICROPHONE",
            "delay": 2
        },
        {
            "text": "Hi team. I think we should first review the requirements and then estimate the development phases. What do you think about using React Native?",
            "source": "🔊 SYSTEM_AUDIO", 
            "delay": 3
        },
        {
            "text": "React Native sounds good. We need to decide on the backend technology as well. I suggest we use Node.js with MongoDB. Also, we should assign team members to different modules.",
            "source": "🎤 MICROPHONE",
            "delay": 3
        },
        {
            "text": "Agreed on the tech stack. For the timeline, I think we can complete the MVP in 8 weeks. John, can you handle the authentication module? Sarah, would you work on the user interface components?",
            "source": "🔊 SYSTEM_AUDIO",
            "delay": 3
        },
        {
            "text": "Yes, I can work on authentication. We should also plan for testing phases and deployment. I recommend we have weekly sprint reviews starting next Monday at 10 AM.",
            "source": "🎤 MICROPHONE",
            "delay": 3
        },
        {
            "text": "Perfect. Let's also budget $50,000 for this project and plan to launch by December 15th. We'll need to coordinate with the marketing team for the launch campaign.",
            "source": "🔊 SYSTEM_AUDIO",
            "delay": 2
        }
    ]
    
    print("\n🎯 Starting simulated meeting conversation...\n")
    
    for i, part in enumerate(conversation_parts, 1):
        print(f"📢 Speaker {i}: {part['text'][:50]}...")
        
        # Simulate processing delay
        time.sleep(1)
        
        # Add transcription to assistant
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        insights = assistant.add_transcription(part["text"], part["source"], timestamp)
        
        # Display insights if generated
        if insights:
            assistant.display_insights(insights)
        
        # Wait between conversation parts
        time.sleep(part["delay"])
    
    print("\n" + "=" * 60)
    print("🏁 Meeting conversation completed!")
    print("=" * 60)
    
    # Display session status
    print("\n📊 Final Meeting Session Status:")
    assistant.get_session_status()
    
    # Generate and save final summary
    print("\n📋 Generating comprehensive meeting summary...")
    summary_file = assistant.end_session()
    
    if summary_file:
        print(f"✅ Meeting summary saved to: {summary_file}")
        
        # Also display some summary statistics
        summary = assistant.summary_manager.load_session_summary(summary_file)
        if summary:
            stats = summary.get("statistics", {})
            print(f"\n📈 Meeting Statistics:")
            print(f"   • Total Transcripts: {stats.get('total_transcripts', 0)}")
            print(f"   • Questions Generated: {stats.get('questions_generated', 0)}")
            print(f"   • Key Points Identified: {stats.get('key_points_identified', 0)}")
            print(f"   • Action Items Captured: {stats.get('action_items_captured', 0)}")
            print(f"   • Decisions Recorded: {stats.get('decisions_recorded', 0)}")
    
    print("\n🎉 Demo completed! Check the generated files for detailed meeting summary.")
    return summary_file


def demonstrate_features():
    """Demonstrate specific features of the meeting assistant."""
    
    print("\n" + "=" * 60)
    print("🔍 FEATURE DEMONSTRATION")
    print("=" * 60)
    
    assistant = MeetingAssistantService(min_text_length=10)
    
    # Test 1: Short text (should not trigger analysis)
    print("\n1. Testing short text handling:")
    result = assistant.add_transcription("Hello", "microphone", "10:00:00")
    if not result:
        print("   ✅ Short text correctly ignored (no AI analysis triggered)")
    
    # Test 2: Context building
    print("\n2. Testing context building with multiple inputs:")
    texts = [
        "We need to discuss the budget for the marketing campaign",
        "The total budget should be around fifty thousand dollars",
        "We should allocate thirty thousand for digital advertising"
    ]
    
    for i, text in enumerate(texts):
        timestamp = f"10:0{i+1}:00"
        result = assistant.add_transcription(text, "microphone", timestamp)
        if result:
            print(f"   📝 Analysis triggered for input {i+1}")
    
    # Test 3: Session statistics
    print("\n3. Session statistics:")
    assistant.get_session_status()
    
    # Clean up
    assistant.end_session()
    print("\n✅ Feature demonstration completed!")


if __name__ == "__main__":
    try:
        # Run the main demo
        summary_file = simulate_meeting_conversation()
        
        # Run feature demonstration
        demonstrate_features()
        
        print(f"\n🎯 Demo Summary:")
        print(f"   • Meeting simulation completed successfully")
        print(f"   • AI insights generated and displayed")
        print(f"   • Summary saved to: {summary_file}")
        print(f"   • Features demonstrated and tested")
        print(f"\n💡 Next Steps:")
        print(f"   • Run 'python main.py' for live meeting assistance")
        print(f"   • Check the meeting_summaries/ directory for saved files")
        print(f"   • Review the generated Markdown summary for easy reading")
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()