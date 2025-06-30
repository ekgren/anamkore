# nano-tools/nano_gemini_cli_core/tools/web_search.py
from openai_agents import function_tool
import litellm
from typing import List, Dict, Any

def _format_search_results(response: Dict[str, Any]) -> str:
    """
    Parses the structured response from a Gemini search-enabled call
    and formats it with inline citations and a source list.
    """
    try:
        message = response['choices'][0]['message']
        if not message.get('content'):
            return "No content found in search results."

        # The gemini-cli does this via a complex grounding metadata object.
        # For our nano version, we will assume a simpler structure is returned
        # via litellm or that the core text content is the most important part.
        # A more advanced implementation would parse the `tool_calls` and
        # grounding metadata if litellm exposes it directly.
        
        # For now, we focus on presenting the text content cleanly.
        # The key is that the API call itself was made correctly.
        
        text_content = message['content']
        
        # A nano-implementation of source listing, assuming sources might be
        # appended or described in the content itself by the model.
        # A full implementation would require deep parsing of grounding metadata.
        
        return f"Web search results:\n\n{text_content}"

    except (KeyError, IndexError, TypeError) as e:
        return f"Error parsing search results: {e}. Raw response: {response}"


@function_tool
def google_web_search(query: str) -> str:
    """
    Performs a web search using the Gemini API's built-in Google Search tool
    and returns a formatted result with sources.

    Args:
        query: The search query to find information on the web.
    """
    if not query or not query.strip():
        return "Error: The 'query' parameter cannot be empty."

    try:
        # This is the correct way to trigger the backend search tool.
        # We are not calling a function, but telling the model it *can*.
        response = litellm.completion(
            model="gemini/gemini-1.5-pro-latest",
            messages=[{"role": "user", "content": query}],
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "google_search",
                        "description": "Performs a Google search and returns a list of websites and their contents.",
                    }
                }
            ],
            # "any" allows the model to choose between a direct answer or using the tool.
            tool_choice="any" 
        )
        
        # The response object from litellm is a dict, not an object
        return _format_search_results(response.dict())

    except Exception as e:
        return f"An unexpected error occurred during the web search: {e}"
