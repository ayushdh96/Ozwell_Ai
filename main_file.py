import gradio as gr
import requests
import json

def load_token(file_path='token.txt'):
    try:
        with open(file_path, 'r') as file:
            token = file.read().strip()
            return token
    except Exception as e:
        raise Exception(f"Error reading token from {file_path}: {e}")

def call_bluehive_api(prompt, system_message, token):
    url = "https://ai.bluehive.com/api/v1/completion"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    payload = {
        "prompt": prompt,
        "systemMessage": system_message
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        return f"HTTP error occurred: {http_err}\nResponse: {response.text}"
    except Exception as err:
        return f"Other error occurred: {err}"

def build_prompt(conversation):
    """
    Convert the conversation list into a single text string.
    Each item in 'conversation' is a tuple (role, text).
    Example: [("user", "Hi"), ("assistant", "Hello!")]
    We'll prefix with 'User:' and 'Assistant:' lines to maintain context.
    """
    prompt_lines = []
    for role, text in conversation:
        if role == "user":
            prompt_lines.append(f"User: {text}")
        elif role == "assistant":
            prompt_lines.append(f"Assistant: {text}")
    return "\n".join(prompt_lines)

def respond(user_input, history):
    """
    Gradio update function. 'history' is the conversation State.
    1. Append the new user message to the conversation.
    2. Build the prompt from the entire conversation.
    3. Call the BlueHive API.
    4. Append the assistant response to the conversation.
    5. Return the updated conversation for display.
    """
    if history is None:
        history = []
    
    # 1. Append user message
    history.append(("user", user_input))
    
    # 2. Build the entire prompt from conversation
    prompt_text = build_prompt(history)
    
    # 3. Call the API
    token = load_token()
    system_message = "You are a helpful chatbot named Will. Always maintain context."
    response = call_bluehive_api(prompt_text, system_message, token)
    
    # If it's an error message (string), just display it.
    if isinstance(response, str):
        bot_reply = response
    else:
        # Extract the assistant message from JSON
        try:
            bot_reply = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            bot_reply = "Invalid response format received."
    
    # 4. Append assistant message
    history.append(("assistant", bot_reply))
    
    # 5. Return updated conversation (for both display and state)
    return history, history

# Build Gradio blocks
with gr.Blocks() as demo:
    gr.Markdown("# BlueHive Conversational Demo")
    chatbot = gr.Chatbot()
    user_input = gr.Textbox(label="Type your message here...")
    state = gr.State([])
    
    # When user submits text, call 'respond' function
    user_input.submit(
        fn=respond,
        inputs=[user_input, state],
        outputs=[chatbot, state]
    )

if __name__ == "__main__":
    demo.launch()