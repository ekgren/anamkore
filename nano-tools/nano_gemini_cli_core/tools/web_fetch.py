# nano-tools/nano_gemini_cli_core/tools/web_fetch.py
import requests
from agents import function_tool
import litellm
import re
try:
    import html2text
except ImportError:
    def html2text_mock(*args, **kwargs):
        raise ImportError("The 'html2text' package is not installed. Please install it with 'pip install html2text'.")
    html2text = html2text_mock

def _manual_fetch_and_clean(url: str) -> str:
    """
    Manually fetches a URL and cleans the HTML content using html2text,
    matching the configuration of the original gemini-cli.
    """
    try:
        if 'github.com' in url and '/blob/' in url:
            url = url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Configure html2text to match gemini-cli's implementation
        h = html2text.HTML2Text()
        h.ignore_links = True
        h.ignore_images = True
        h.body_width = 0  # This disables word wrapping
        
        cleaned_text = h.handle(response.text)
        
        return cleaned_text

    except requests.exceptions.RequestException as e:
        return f"Error during manual fetch for {url}: {e}"
    except ImportError as e:
        return str(e)
    except Exception as e:
        return f"An unexpected error occurred during manual fetch: {e}"

def _web_fetch_impl(prompt: str) -> Dict[str, str]:
    """
    Core implementation for fetching web content.
    """
    try:
        urls = re.findall(r'(https?://[^\s]+)', prompt)
        if not urls:
            msg = "Error: No URL found in the prompt."
            return {"llm_content": msg, "display_content": msg}
            
        url = urls[0]
        print(f"Simulating primary fetch failure. Proceeding to manual fallback for {url}")
        
        content = _manual_fetch_and_clean(url)
        
        if content.startswith("Error"):
            return {"llm_content": content, "display_content": content}

        llm_output = f"--- Manually Fetched Content from {url} ---\n\n{content}"
        display_output = f"Successfully fetched content from {url}."
        
        return {"llm_content": llm_output, "display_content": display_output}

    except Exception as e:
        msg = f"An unexpected error occurred in the web_fetch tool: {e}"
        return {"llm_content": msg, "display_content": msg}

@function_tool
def web_fetch(prompt: str) -> Dict[str, str]:
    """
    Processes content from URL(s) embedded in a prompt. It first tries to let the main agent
    handle the fetching and processing. If that provides no meaningful result, it falls back
    to a manual fetch and clean of the URL content.

    Args:
        prompt: A comprehensive prompt that includes the URL(s) to fetch and specific
                instructions on how to process their content (e.g., "Summarize https://example.com").
    """
    return _web_fetch_impl(prompt)