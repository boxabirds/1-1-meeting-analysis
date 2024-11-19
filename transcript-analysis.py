import argparse
import sys
from pathlib import Path
import os
import google.generativeai as genai

def estimate_invocation_cost(usage_metadata) -> float:
    """
    Estimates the cost of a Gemini API invocation based on token usage.

    Args:
        usage_metadata : The usage metadata from the API response.
            It should contain 'promptTokenCount' and 'candidatesTokenCount'.

    Returns:
        float: The estimated cost of the invocation in USD.

    Pricing information:
    - For prompts up to 128k tokens:
      - Input: $0.075 per 1 million tokens
      - Output: $0.30 per 1 million tokens
    - For prompts longer than 128k tokens:
      - Input: $0.15 per 1 million tokens
      - Output: $0.60 per 1 million tokens

    Source: [Google AI Pricing](https://ai.google.dev/pricing#1_5flash)
    """
    prompt_token_count = usage_metadata.prompt_token_count
    candidates_token_count = usage_metadata.candidates_token_count
    total_token_count = prompt_token_count + candidates_token_count

    input_cost_per_million_tokens = 0.075 if total_token_count <= 128000 else 0.15
    output_cost_per_million_tokens = 0.30 if total_token_count <= 128000 else 0.60

    input_cost = (prompt_token_count / 1e6) * input_cost_per_million_tokens
    output_cost = (candidates_token_count / 1e6) * output_cost_per_million_tokens

    return input_cost + output_cost

def analyze_call_gemini(transcription_text):
    """Analyzes a call transcription using Gemini."""
    
    # Configure the API key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")
    
    summary_prompt = f"""Summarisation:
    - Provide a 1-paragraph summary of the following discussion.
    - List the main topics discussed.
    - Specify any actions agreed upon.

    Metrics:
    - Calculate the overall ratio of talk time between the two speakers. Express this as a ratio (e.g., Speaker A:Speaker B = 2:1).

    Feedback:
    - Identify aspects of the call that went well.
    - Suggest improvements for the next call.

    Discussion:
    {transcription_text}
    """

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content([{"text": summary_prompt}])
    
    analysis = response.text
    
    usage_metadata = response.usage_metadata
    cost = estimate_invocation_cost(usage_metadata)
    
    return analysis, cost

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze a transcript using Gemini.")
    parser.add_argument("txt_file", help="Path to the .txt file.")
    parser.add_argument("--output", help="Path to the output file.")
    args = parser.parse_args()

    input_path = Path(args.txt_file)
    output_path = Path(args.output) if args.output else input_path.with_suffix('.analysis.md')

    try:
        with open(args.txt_file, 'r', encoding='utf-8') as f:
            transcription_text = f.read()
    except FileNotFoundError:
        print(f"Error: File '{args.txt_file}' not found.", file=sys.stderr)
        sys.exit(1)

    analysis, cost = analyze_call_gemini(transcription_text)
    
    with open(output_path, 'w') as f:
        f.write(analysis)
    
    print(f"Analysis written to {output_path}")
    
    if cost is not None:
        print(f"Estimated cost of parsing: ${cost:.6f}")
    else:
        print("Unable to estimate cost (usage metadata not available)")
