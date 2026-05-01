import sys
import os
from llm_client import LLMClient
from fb_client import FBClient

def test_formatting():
    print("Testing social media formatting...")
    llm = LLMClient()
    topic = "Magnesium L-Threonate for Synaptic Density"
    context = "Magnesium L-threonate (MgT) is a form of magnesium that effectively crosses the blood-brain barrier. Studies show it increases synapse density in the hippocampus."

    post = llm.create_biohacking_post(topic, context)
    print("\n--- GENERATED POST ---")
    print(post)
    print("----------------------\n")

    # Check for mandatory elements
    if topic.upper() not in post.upper():
        print("FAIL: Topic not in title (or not ALL CAPS)")
    if "MECHANICS" not in post:
        print("FAIL: 'MECHANICS' header missing")
    if "BIOLOGICAL LEVERAGE" not in post:
        print("FAIL: 'BIOLOGICAL LEVERAGE' header missing")
    if "TACTICAL IMPLEMENTATION" not in post:
        print("FAIL: 'TACTICAL IMPLEMENTATION' header missing")
    if "Do your own research. Don't be a statistic." not in post:
        print("FAIL: Mandatory sign-off missing")

    print("Social media formatting test complete.")

if __name__ == "__main__":
    test_formatting()
