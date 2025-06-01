#!/usr/bin/env python3
"""
Comprehensive 100-Question Test Runner for Batman Chatbot
Phase 4: Testing & Refinement

The ultimate test of our Batman chatbot's capabilities!
"""

import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple

# Add chatbot core to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'chatbot'))
from core.batman_chatbot import BatmanChatbot, BatmanResponse

class ComprehensiveTestRunner:
    """The ultimate 100-question test runner for Batman chatbot."""
    
    def __init__(self):
        """Initialize the comprehensive test runner."""
        self.chatbot = BatmanChatbot("/home/traxx/batman_chatbot/database/batman_universe.db")
        self.test_questions = self._load_all_test_questions()
        self.results = []
        
    def _load_all_test_questions(self) -> List[Dict]:
        """Load all 100 test questions organized by category."""
        
        # Standard Questions (Basic Information Retrieval) - Questions 1-25
        standard_questions = [
            {"id": 1, "question": "Who is Batman?", "category": "standard", "expected_type": "character"},
            {"id": 2, "question": "What is the Batmobile?", "category": "standard", "expected_type": "vehicle"},
            {"id": 3, "question": "Where is Gotham City located?", "category": "standard", "expected_type": "location"},
            {"id": 4, "question": "Can you tell me about the Joker?", "category": "standard", "expected_type": "character"},
            {"id": 5, "question": "What vehicles does Batman use?", "category": "standard", "expected_type": "multi_entity"},
            {"id": 6, "question": "Who are the members of the Bat Family?", "category": "standard", "expected_type": "relationship"},
            {"id": 7, "question": "What is Arkham Asylum?", "category": "standard", "expected_type": "location"},
            {"id": 8, "question": "Describe Wayne Manor.", "category": "standard", "expected_type": "location"},
            {"id": 9, "question": "What is the storyline of The Dark Knight Returns?", "category": "standard", "expected_type": "storyline"},
            {"id": 10, "question": "Who founded the Justice League?", "category": "standard", "expected_type": "character"},
            {"id": 11, "question": "What is the Batwing?", "category": "standard", "expected_type": "vehicle"},
            {"id": 12, "question": "Tell me about Robin.", "category": "standard", "expected_type": "character"},
            {"id": 13, "question": "Where does Catwoman usually operate?", "category": "standard", "expected_type": "location"},
            {"id": 14, "question": "What is the purpose of the Batcave?", "category": "standard", "expected_type": "location"},
            {"id": 15, "question": "Who is Alfred Pennyworth?", "category": "standard", "expected_type": "character"},
            {"id": 16, "question": "What vehicles are stored in the Batcave?", "category": "standard", "expected_type": "multi_entity"},
            {"id": 17, "question": "What is the Court of Owls?", "category": "standard", "expected_type": "organization"},
            {"id": 18, "question": "Can you list all the villains in Gotham City?", "category": "standard", "expected_type": "multi_entity"},
            {"id": 19, "question": "What is the setting of Batman: Year One?", "category": "standard", "expected_type": "storyline"},
            {"id": 20, "question": "Who is Commissioner Gordon?", "category": "standard", "expected_type": "character"},
            {"id": 21, "question": "What is Bane?", "category": "standard", "expected_type": "character"},
            {"id": 22, "question": "Tell me about Two-Face.", "category": "standard", "expected_type": "character"},
            {"id": 23, "question": "What is the Penguin like?", "category": "standard", "expected_type": "character"},
            {"id": 24, "question": "Who is Nightwing?", "category": "standard", "expected_type": "character"},
            {"id": 25, "question": "What is the Riddler known for?", "category": "standard", "expected_type": "character"}
        ]
        
        # Detailed and Specific Questions - Questions 26-50
        detailed_questions = [
            {"id": 26, "question": "What is the origin story of Bane?", "category": "detailed", "expected_type": "character"},
            {"id": 27, "question": "Which vehicle did Batman use in The Killing Joke?", "category": "detailed", "expected_type": "vehicle"},
            {"id": 28, "question": "What is the exact address of Wayne Enterprises in Gotham?", "category": "detailed", "expected_type": "location"},
            {"id": 29, "question": "How many Robins have there been, and who are they?", "category": "detailed", "expected_type": "multi_entity"},
            {"id": 30, "question": "What is the significance of Crime Alley in Batman's history?", "category": "detailed", "expected_type": "location"},
            {"id": 31, "question": "Can you describe the interior of Blackgate Prison?", "category": "detailed", "expected_type": "location"},
            {"id": 32, "question": "What role does Lucius Fox play in Batman's operations?", "category": "detailed", "expected_type": "character"},
            {"id": 33, "question": "What is the primary function of the Batboat?", "category": "detailed", "expected_type": "vehicle"},
            {"id": 34, "question": "Who are the key members of the League of Assassins?", "category": "detailed", "expected_type": "organization"},
            {"id": 35, "question": "What happens to Jason Todd in A Death in the Family?", "category": "detailed", "expected_type": "storyline"},
            {"id": 36, "question": "What is the history of the Red Hood?", "category": "detailed", "expected_type": "character"},
            {"id": 37, "question": "Which locations in Gotham are controlled by Penguin?", "category": "detailed", "expected_type": "multi_entity"},
            {"id": 38, "question": "What is the Batcycle's top speed?", "category": "detailed", "expected_type": "vehicle"},
            {"id": 39, "question": "Who designed the Batcomputer?", "category": "detailed", "expected_type": "character"},
            {"id": 40, "question": "What is the connection between Ra's al Ghul and Talia al Ghul?", "category": "detailed", "expected_type": "relationship"},
            {"id": 41, "question": "Can you list all the gadgets stored in the Batmobile?", "category": "detailed", "expected_type": "multi_entity"},
            {"id": 42, "question": "What is the architectural style of Wayne Manor?", "category": "detailed", "expected_type": "location"},
            {"id": 43, "question": "How does the storyline of Hush involve Tommy Elliot?", "category": "detailed", "expected_type": "storyline"},
            {"id": 44, "question": "Who are the minor villains in No Man's Land?", "category": "detailed", "expected_type": "multi_entity"},
            {"id": 45, "question": "What is the significance of the Batcave's trophy room?", "category": "detailed", "expected_type": "location"},
            {"id": 46, "question": "Tell me about Harvey Dent.", "category": "detailed", "expected_type": "character"},
            {"id": 47, "question": "What is Scarecrow's real name?", "category": "detailed", "expected_type": "character"},
            {"id": 48, "question": "Where is the Iceberg Lounge located?", "category": "detailed", "expected_type": "location"},
            {"id": 49, "question": "What weapons does the Batmobile have?", "category": "detailed", "expected_type": "vehicle"},
            {"id": 50, "question": "Who is Oracle in the Batman universe?", "category": "detailed", "expected_type": "character"}
        ]
        
        # Comparative and Analytical Questions - Questions 51-75
        comparative_questions = [
            {"id": 51, "question": "Who is faster: Batman or Nightwing?", "category": "comparative", "expected_type": "comparative_analysis"},
            {"id": 52, "question": "Which is more armored: the Batmobile or the Batwing?", "category": "comparative", "expected_type": "comparative_analysis"},
            {"id": 53, "question": "Who is smarter: Batman or Lex Luthor?", "category": "comparative", "expected_type": "comparative_analysis"},
            {"id": 54, "question": "What's the difference between Arkham Asylum and Blackgate Prison?", "category": "comparative", "expected_type": "comparative_analysis"},
            {"id": 55, "question": "How do the skills of Robin compare to Batgirl?", "category": "comparative", "expected_type": "comparative_analysis"},
            {"id": 56, "question": "Which villain is more dangerous: Joker or Bane?", "category": "comparative", "expected_type": "comparative_analysis"},
            {"id": 57, "question": "What are the differences between Batman's and Superman's methods?", "category": "comparative", "expected_type": "comparative_analysis"},
            {"id": 58, "question": "How does Gotham City compare to Metropolis?", "category": "comparative", "expected_type": "comparative_analysis"},
            {"id": 59, "question": "Which Robin became Nightwing?", "category": "comparative", "expected_type": "character"},
            {"id": 60, "question": "Who has been Robin the longest?", "category": "comparative", "expected_type": "character"},
            {"id": 61, "question": "What's the relationship between Catwoman and Batman?", "category": "comparative", "expected_type": "relationship"},
            {"id": 62, "question": "How do the Bat-vehicles differ in their purposes?", "category": "comparative", "expected_type": "multi_entity"},
            {"id": 63, "question": "Which organization is more secretive: Court of Owls or League of Assassins?", "category": "comparative", "expected_type": "comparative_analysis"},
            {"id": 64, "question": "What are the similarities between Two-Face and Penguin?", "category": "comparative", "expected_type": "comparative_analysis"},
            {"id": 65, "question": "How does Batman's relationship with Alfred differ from his relationship with Gordon?", "category": "comparative", "expected_type": "relationship"},
            {"id": 66, "question": "Which storyline is darker: The Killing Joke or A Death in the Family?", "category": "comparative", "expected_type": "comparative_analysis"},
            {"id": 67, "question": "What's the difference between the various Batcaves?", "category": "comparative", "expected_type": "location"},
            {"id": 68, "question": "How do Batman's early years compare to his modern era?", "category": "comparative", "expected_type": "comparative_analysis"},
            {"id": 69, "question": "Which vehicle is Batman's primary mode of transportation?", "category": "comparative", "expected_type": "vehicle"},
            {"id": 70, "question": "What are the key differences between the various Joker origin stories?", "category": "comparative", "expected_type": "comparative_analysis"},
            {"id": 71, "question": "Who is stronger: Batman or Bane?", "category": "comparative", "expected_type": "comparative_analysis"},
            {"id": 72, "question": "Batman vs Joker: who wins in a fight?", "category": "comparative", "expected_type": "comparative_analysis"},
            {"id": 73, "question": "Which is faster: Batmobile or Batcycle?", "category": "comparative", "expected_type": "comparative_analysis"},
            {"id": 74, "question": "Who is more intelligent: Riddler or Batman?", "category": "comparative", "expected_type": "comparative_analysis"},
            {"id": 75, "question": "What's better: Batman's technology or his detective skills?", "category": "comparative", "expected_type": "comparative_analysis"}
        ]
        
        # Edge Cases and Complex Queries - Questions 76-100
        edge_case_questions = [
            {"id": 76, "question": "Tell me about all Batman vehicles.", "category": "edge_case", "expected_type": "multi_entity"},
            {"id": 77, "question": "List all characters in Gotham City.", "category": "edge_case", "expected_type": "multi_entity"},
            {"id": 78, "question": "Show me every location in the Batman universe.", "category": "edge_case", "expected_type": "multi_entity"},
            {"id": 79, "question": "Who are Batman's enemies?", "category": "edge_case", "expected_type": "relationship"},
            {"id": 80, "question": "What are Batman's allies?", "category": "edge_case", "expected_type": "relationship"},
            {"id": 81, "question": "Btmn", "category": "edge_case", "expected_type": "character"},  # Typo test
            {"id": 82, "question": "Jokr", "category": "edge_case", "expected_type": "character"},  # Typo test
            {"id": 83, "question": "Batmobil", "category": "edge_case", "expected_type": "vehicle"},  # Typo test
            {"id": 84, "question": "Gothm City", "category": "edge_case", "expected_type": "location"},  # Typo test
            {"id": 85, "question": "Who is the Dark Knight?", "category": "edge_case", "expected_type": "character"},
            {"id": 86, "question": "What is the Caped Crusader?", "category": "edge_case", "expected_type": "character"},
            {"id": 87, "question": "Who is the World's Greatest Detective?", "category": "edge_case", "expected_type": "character"},
            {"id": 88, "question": "Tell me about the Clown Prince of Crime.", "category": "edge_case", "expected_type": "character"},
            {"id": 89, "question": "What is the City of Gotham?", "category": "edge_case", "expected_type": "location"},
            {"id": 90, "question": "Who lives in Wayne Manor?", "category": "edge_case", "expected_type": "character"},
            {"id": 91, "question": "What's in the Batcave?", "category": "edge_case", "expected_type": "multi_entity"},
            {"id": 92, "question": "Tell me about Bruce Wayne.", "category": "edge_case", "expected_type": "character"},
            {"id": 93, "question": "What does Batman drive?", "category": "edge_case", "expected_type": "vehicle"},
            {"id": 94, "question": "Where does Batman live?", "category": "edge_case", "expected_type": "location"},
            {"id": 95, "question": "Who helps Batman?", "category": "edge_case", "expected_type": "relationship"},
            {"id": 96, "question": "What is Batman's car called?", "category": "edge_case", "expected_type": "vehicle"},
            {"id": 97, "question": "Where is Batman's base?", "category": "edge_case", "expected_type": "location"},
            {"id": 98, "question": "Who trained Batman?", "category": "edge_case", "expected_type": "character"},
            {"id": 99, "question": "What is Batman's weakness?", "category": "edge_case", "expected_type": "character"},
            {"id": 100, "question": "Why does Batman fight crime?", "category": "edge_case", "expected_type": "character"}
        ]
        
        # Combine all questions
        all_questions = standard_questions + detailed_questions + comparative_questions + edge_case_questions
        return all_questions
    
    def run_comprehensive_test(self, max_questions: int = 100) -> Dict:
        """Run the comprehensive 100-question test suite."""
        print("🦇" * 20)
        print("🧪 BATMAN CHATBOT COMPREHENSIVE TEST SUITE")
        print("🦇" * 20)
        print(f"Testing {min(max_questions, len(self.test_questions))} questions across all categories")
        print("Categories: Standard, Detailed, Comparative, Edge Cases")
        print("=" * 80)
        
        start_time = time.time()
        category_stats = {
            'standard': {'total': 0, 'success': 0, 'confidence_sum': 0},
            'detailed': {'total': 0, 'success': 0, 'confidence_sum': 0},
            'comparative': {'total': 0, 'success': 0, 'confidence_sum': 0},
            'edge_case': {'total': 0, 'success': 0, 'confidence_sum': 0}
        }
        
        total_successful = 0
        total_confidence = 0.0
        
        for i, test_case in enumerate(self.test_questions[:max_questions]):
            question_id = test_case['id']
            question = test_case['question']
            category = test_case['category']
            expected_type = test_case['expected_type']
            
            print(f"\n[{question_id}/100] {question}")
            print(f"Category: {category.upper()} | Expected: {expected_type}")
            print("-" * 60)
            
            # Get response from chatbot
            response = self.chatbot.process_query(question)
            
            # Evaluate response
            success = self._evaluate_response(test_case, response)
            if success:
                total_successful += 1
                category_stats[category]['success'] += 1
            
            category_stats[category]['total'] += 1
            category_stats[category]['confidence_sum'] += response.confidence
            total_confidence += response.confidence
            
            # Store result
            result = {
                "question_id": question_id,
                "question": question,
                "category": category,
                "expected_type": expected_type,
                "actual_type": response.query_type,
                "answer": response.answer[:300] + "..." if len(response.answer) > 300 else response.answer,
                "full_answer": response.answer,
                "confidence": response.confidence,
                "success": success,
                "source_entities": response.source_entities,
                "suggestions": response.suggestions or []
            }
            
            self.results.append(result)
            
            # Print result summary
            status = "✅" if success else "❌"
            type_match = "✅" if response.query_type == expected_type or self._is_acceptable_type(expected_type, response.query_type) else "⚠️"
            
            print(f"{status} Success | {type_match} Type | 📊 Confidence: {response.confidence:.1%}")
            print(f"🦇 Response: {response.answer[:150]}{'...' if len(response.answer) > 150 else ''}")
            
            if response.suggestions:
                print(f"💡 Suggestions: {', '.join(response.suggestions[:3])}")
            
            print("=" * 60)
            
            # Brief pause to avoid overwhelming output
            time.sleep(0.1)
        
        end_time = time.time()
        
        # Calculate comprehensive statistics
        summary = self._generate_comprehensive_summary(
            total_successful, total_confidence, max_questions, 
            end_time - start_time, category_stats
        )
        
        self._print_comprehensive_summary(summary)
        self._save_comprehensive_results(summary)
        
        return summary
    
    def _evaluate_response(self, test_case: Dict, response: BatmanResponse) -> bool:
        """Evaluate if a response is successful."""
        # Basic success criteria
        if response.confidence == 0.0:
            return False
        
        if "I don't have information" in response.answer or "I couldn't find" in response.answer:
            return False
            
        if len(response.answer) < 30:  # Very short answers are likely not helpful
            return False
        
        # Type-specific evaluation
        expected_type = test_case['expected_type']
        actual_type = response.query_type
        
        # Allow flexible type matching
        if self._is_acceptable_type(expected_type, actual_type):
            return True
        
        # For comparative questions, accept any reasonable response
        if test_case['category'] == 'comparative' and response.confidence > 0.5:
            return True
        
        # For edge cases (typos), accept if we found something
        if test_case['category'] == 'edge_case' and response.confidence > 0.6:
            return True
            
        return False
    
    def _is_acceptable_type(self, expected: str, actual: str) -> bool:
        """Check if actual response type is acceptable for expected type."""
        type_mappings = {
            'character': ['character_lookup', 'general_search'],
            'vehicle': ['vehicle_lookup', 'general_search'],
            'location': ['location_lookup', 'general_search'],
            'organization': ['general_search', 'character_lookup'],
            'storyline': ['general_search'],
            'multi_entity': ['multi_entity_query', 'general_search', 'relationship_query'],
            'relationship': ['relationship_query', 'general_search', 'multi_entity_query'],
            'comparative_analysis': ['comparative_analysis', 'general_search', 'character_lookup']
        }
        
        acceptable_types = type_mappings.get(expected, [expected])
        return actual in acceptable_types
    
    def _generate_comprehensive_summary(self, successful: int, total_confidence: float, 
                                       total_questions: int, total_time: float, 
                                       category_stats: Dict) -> Dict:
        """Generate comprehensive test summary."""
        summary = {
            "total_questions": total_questions,
            "successful_responses": successful,
            "success_rate": successful / total_questions,
            "average_confidence": total_confidence / total_questions,
            "total_time": total_time,
            "questions_per_second": total_questions / total_time,
            "category_breakdown": {}
        }
        
        # Calculate category breakdowns
        for category, stats in category_stats.items():
            if stats['total'] > 0:
                summary["category_breakdown"][category] = {
                    "total_questions": stats['total'],
                    "successful": stats['success'],
                    "success_rate": stats['success'] / stats['total'],
                    "average_confidence": stats['confidence_sum'] / stats['total']
                }
        
        return summary
    
    def _print_comprehensive_summary(self, summary: Dict):
        """Print comprehensive test summary."""
        print("\n" + "🦇" * 20)
        print("🎯 BATMAN CHATBOT COMPREHENSIVE TEST RESULTS")
        print("🦇" * 20)
        
        print(f"📊 OVERALL PERFORMANCE:")
        print(f"   Total Questions: {summary['total_questions']}")
        print(f"   Successful Responses: {summary['successful_responses']}")
        print(f"   Success Rate: {summary['success_rate']:.1%}")
        print(f"   Average Confidence: {summary['average_confidence']:.1%}")
        print(f"   Total Time: {summary['total_time']:.1f}s")
        print(f"   Speed: {summary['questions_per_second']:.1f} questions/second")
        
        print(f"\n📈 CATEGORY BREAKDOWN:")
        for category, stats in summary["category_breakdown"].items():
            emoji = {"standard": "📚", "detailed": "🔍", "comparative": "⚖️", "edge_case": "🎯"}
            print(f"   {emoji.get(category, '📋')} {category.upper()}: {stats['success_rate']:.1%} success ({stats['successful']}/{stats['total_questions']}) | Avg Confidence: {stats['average_confidence']:.1%}")
        
        # Performance grade
        overall_score = summary['success_rate']
        if overall_score >= 0.9:
            grade = "🏆 LEGENDARY"
            message = "BATMAN HIMSELF WOULD BE PROUD!"
        elif overall_score >= 0.8:
            grade = "🥇 EXCELLENT"
            message = "World-class Batman expert performance!"
        elif overall_score >= 0.7:
            grade = "🥈 VERY GOOD" 
            message = "Strong Batman knowledge with room for improvement!"
        elif overall_score >= 0.6:
            grade = "🥉 GOOD"
            message = "Solid foundation, needs refinement!"
        elif overall_score >= 0.5:
            grade = "⚠️ NEEDS IMPROVEMENT"
            message = "Basic functionality working, requires optimization!"
        else:
            grade = "❌ POOR"
            message = "Significant improvements needed!"
            
        print(f"\n🎖️ FINAL GRADE: {grade}")
        print(f"🦇 {message}")
        
        # Interesting insights
        print(f"\n💡 KEY INSIGHTS:")
        best_category = max(summary["category_breakdown"].items(), key=lambda x: x[1]['success_rate'])
        worst_category = min(summary["category_breakdown"].items(), key=lambda x: x[1]['success_rate'])
        
        print(f"   🏆 Best Category: {best_category[0].upper()} ({best_category[1]['success_rate']:.1%})")
        print(f"   📈 Worst Category: {worst_category[0].upper()} ({worst_category[1]['success_rate']:.1%})")
        
        if summary['average_confidence'] > 0.8:
            print(f"   🎯 High confidence across responses!")
        elif summary['average_confidence'] > 0.6:
            print(f"   📊 Moderate confidence levels.")
        else:
            print(f"   ⚠️ Low confidence suggests uncertainty in responses.")
    
    def _save_comprehensive_results(self, summary: Dict):
        """Save comprehensive test results to JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comprehensive_test_results_{timestamp}.json"
        
        full_results = {
            "test_metadata": {
                "test_name": "Batman Chatbot Comprehensive 100-Question Test",
                "timestamp": timestamp,
                "chatbot_version": "Phase 4 - Conversation Intelligence",
                "total_entities": 1056,
                "test_categories": ["standard", "detailed", "comparative", "edge_case"]
            },
            "summary": summary,
            "individual_results": self.results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(full_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 Comprehensive results saved to: {filename}")
    
    def get_failed_questions_analysis(self) -> Dict:
        """Analyze failed questions for insights."""
        failed_questions = [r for r in self.results if not r["success"]]
        
        if not failed_questions:
            return {"message": "🎉 NO FAILED QUESTIONS! PERFECT PERFORMANCE!"}
        
        # Analyze failure patterns
        failure_by_category = {}
        failure_by_type = {}
        low_confidence_questions = []
        
        for result in failed_questions:
            category = result["category"]
            expected_type = result["expected_type"]
            
            failure_by_category[category] = failure_by_category.get(category, 0) + 1
            failure_by_type[expected_type] = failure_by_type.get(expected_type, 0) + 1
            
            if result["confidence"] < 0.3:
                low_confidence_questions.append(result)
        
        return {
            "total_failed": len(failed_questions),
            "failure_by_category": failure_by_category,
            "failure_by_type": failure_by_type,
            "low_confidence_count": len(low_confidence_questions),
            "sample_failures": failed_questions[:5]  # Show first 5 failures
        }
    
    def close(self):
        """Close chatbot connection."""
        self.chatbot.close()

def main():
    """Run the comprehensive Batman chatbot test."""
    print("🦇 Welcome to the Ultimate Batman Chatbot Test!")
    print("🧪 Preparing to test 100 carefully crafted questions...")
    print("⏰ This may take a few minutes. Grab some coffee and enjoy the show!")
    
    test_runner = ComprehensiveTestRunner()
    
    try:
        # Run the comprehensive test
        summary = test_runner.run_comprehensive_test(max_questions=100)
        
        # Analyze failures
        failure_analysis = test_runner.get_failed_questions_analysis()
        
        if failure_analysis.get("total_failed", 0) > 0:
            print(f"\n🔍 FAILURE ANALYSIS:")
            print(f"   Total Failed: {failure_analysis['total_failed']}")
            print(f"   By Category: {failure_analysis['failure_by_category']}")
            print(f"   Low Confidence: {failure_analysis['low_confidence_count']}")
        
        return 0 if summary['success_rate'] >= 0.7 else 1
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        test_runner.close()

if __name__ == "__main__":
    exit(main())