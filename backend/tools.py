"""
Practice problems tool for CodeCoach.
Returns LeetCode-style problems matching CTCI Arrays & Strings topics.
"""

import random
from livekit.agents import function_tool

# Problems curated from CTCI + LeetCode
PROBLEMS = {
    "arrays": {
        "easy": [
            {"title": "Two Sum", "lc": "#1",
             "desc": "Find two numbers that add up to target.",
             "hint": "Use a hash map to store complements."},
            {"title": "Remove Duplicates", "lc": "#26",
             "desc": "Remove duplicates in-place from sorted array.",
             "hint": "Two pointers - read and write positions."},
            {"title": "Best Time to Buy and Sell Stock", "lc": "#121",
             "desc": "Find max profit from one buy and sell.",
             "hint": "Track min price seen, calculate profit at each step."},
        ],
        "medium": [
            {"title": "3Sum", "lc": "#15",
             "desc": "Find all triplets that sum to zero.",
             "hint": "Sort first, then fix one element and use two pointers."},
            {"title": "Container With Most Water", "lc": "#11",
             "desc": "Find two lines forming container with most water.",
             "hint": "Two pointers from ends, move the shorter one."},
            {"title": "Product of Array Except Self", "lc": "#238",
             "desc": "Each element = product of all others, no division.",
             "hint": "Use prefix and suffix products."},
        ],
        "hard": [
            {"title": "Trapping Rain Water", "lc": "#42",
             "desc": "Calculate trapped water between bars.",
             "hint": "Water at each position = min(maxLeft, maxRight) - height."},
            {"title": "First Missing Positive", "lc": "#41",
             "desc": "Find smallest missing positive in O(n) time, O(1) space.",
             "hint": "Use array itself as hash map."},
        ],
    },
    "strings": {
        "easy": [
            {"title": "Valid Anagram", "lc": "#242",
             "desc": "Check if two strings are anagrams.",
             "hint": "Count character frequencies."},
            {"title": "Reverse String", "lc": "#344",
             "desc": "Reverse string in-place.",
             "hint": "Two pointers swapping from both ends."},
        ],
        "medium": [
            {"title": "Longest Substring Without Repeating", "lc": "#3",
             "desc": "Find longest substring with unique characters.",
             "hint": "Sliding window with a set."},
            {"title": "Group Anagrams", "lc": "#49",
             "desc": "Group strings that are anagrams.",
             "hint": "Sorted string as hash key."},
        ],
        "hard": [
            {"title": "Minimum Window Substring", "lc": "#76",
             "desc": "Find minimum window containing all chars of target.",
             "hint": "Sliding window with char frequency tracking."},
        ],
    },
    "hash_tables": {
        "easy": [
            {"title": "Two Sum", "lc": "#1",
             "desc": "Find two numbers that add to target.",
             "hint": "Store complement as you iterate."},
            {"title": "Contains Duplicate", "lc": "#217",
             "desc": "Check if array has duplicates.",
             "hint": "Use a set."},
        ],
        "medium": [
            {"title": "Top K Frequent Elements", "lc": "#347",
             "desc": "Find k most frequent elements.",
             "hint": "Count with hash map, then heap or bucket sort."},
            {"title": "Subarray Sum Equals K", "lc": "#560",
             "desc": "Count subarrays that sum to k.",
             "hint": "Prefix sum + hash map."},
        ],
    },
}


@function_tool
async def get_practice_problems(topic: str, difficulty: str) -> str:
    """
    Get a practice problem for interview prep.
    
    Args:
        topic: 'arrays', 'strings', or 'hash_tables'
        difficulty: 'easy', 'medium', or 'hard'
    """
    # Normalizing the input
    topic = topic.lower().strip().replace(" ", "_").replace("-", "_")
    difficulty = difficulty.lower().strip()
    
    # Handling common variations
    aliases = {
        "array": "arrays",
        "string": "strings", 
        "hash_table": "hash_tables",
        "hashmap": "hash_tables",
        "hashing": "hash_tables",
    }
    topic = aliases.get(topic, topic)
    
    if topic not in PROBLEMS:
        return f"Available topics: {', '.join(PROBLEMS.keys())}"
    
    if difficulty not in PROBLEMS[topic]:
        return f"Available for {topic}: {', '.join(PROBLEMS[topic].keys())}"
    
    p = random.choice(PROBLEMS[topic][difficulty])
    
    # Returning a voice-friendly output
    return (
        f"Here's a {difficulty} {topic} problem: {p['title']}, LeetCode {p['lc']}. "
        f"{p['desc']} "
        f"Hint: {p['hint']} "
        f"Want me to explain the approach?"
    )
