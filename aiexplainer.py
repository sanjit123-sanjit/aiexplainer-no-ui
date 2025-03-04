import requests
import base64
import pyautogui
from PIL import Image
import io
import json
import tkinter as tk

def get_terminal_inputs():
    """
    Prompts the user in the terminal for required parameters.
    Returns a tuple of (prompt_prefix, api_key, base_url, model_name, ai_name).
    """
    prompt_prefix = input("Enter the prompt prefix (e.g., 'describe this image'): ").strip()
    api_key = input("Enter your API key: ").strip()
    base_url = input("Enter the Base URL for the AI API Endpoint (e.g., https://generativelanguage.googleapis.com/v1beta/openai/chat/completions): ").strip()
    model_name = input("Enter the Image AI Model Name you want to use: ").strip()
    ai_name = input("Enter the AI Name (optional, for display purposes): ").strip()
    return prompt_prefix, api_key, base_url, model_name, ai_name

def select_region():
    """
    Opens a full-screen transparent Tkinter window to let the user select a region.
    Returns a tuple (x, y, width, height) representing the selected region.
    """
    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.attributes("-alpha", 0.3)
    root.config(bg="black")

    canvas = tk.Canvas(root, cursor="cross", bg="gray")
    canvas.pack(fill=tk.BOTH, expand=True)

    rect = None
    start_x, start_y = None, None
    region = None

    def on_button_press(event):
        nonlocal start_x, start_y, rect
        start_x, start_y = event.x, event.y
        rect = canvas.create_rectangle(start_x, start_y, start_x, start_y, outline="red", width=2)

    def on_move_press(event):
        nonlocal rect
        canvas.coords(rect, start_x, start_y, event.x, event.y)

    def on_button_release(event):
        nonlocal region
        end_x, end_y = event.x, event.y
        x1 = min(start_x, end_x)
        y1 = min(start_y, end_y)
        x2 = max(start_x, end_x)
        y2 = max(start_y, end_y)
        region = (x1, y1, x2 - x1, y2 - y1)
        root.destroy()

    canvas.bind("<ButtonPress-1>", on_button_press)
    canvas.bind("<B1-Motion>", on_move_press)
    canvas.bind("<ButtonRelease-1>", on_button_release)

    root.mainloop()
    return region

def capture_screenshot_with_region():
    """Captures a screenshot of the region selected by the user."""
    print("Please select the region to capture (click and drag).")
    region = select_region()
    if region:
        print(f"Region selected: {region}")
        screenshot = pyautogui.screenshot(region=region)
        print("Screenshot captured successfully.")
        return screenshot
    else:
        print("No region selected. Capturing full screen.")
        return pyautogui.screenshot()

def encode_image_to_base64(image: Image.Image) -> str:
    """Encodes a PIL Image to a base64 string in PNG format."""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def get_ai_answer(api_key: str, base_url: str, model_name: str, prompt_prefix: str, screenshot: Image.Image) -> str:
    """
    Sends the prompt and screenshot to the Gemini API.
    The image is embedded as a base64 data URL in the message payload.
    """
    api_endpoint = base_url  # The base URL already points to the desired endpoint.
    print(f"Using API endpoint: {api_endpoint}")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Encode the screenshot and create a data URL.
    base64_image = encode_image_to_base64(screenshot)
    image_data_url = f"data:image/png;base64,{base64_image}"

    # Build the JSON payload (using an OpenAI-compatible message format).
    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_prefix},
                    {"type": "image_url", "image_url": {"url": image_data_url}}
                ]
            }
        ]
    }

    try:
        response = requests.post(api_endpoint, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        # Extract the answer from the response (adjust extraction based on your API's response format).
        answer = result.get("choices", [{}])[0].get("message", {}).get("content", "No answer in response")
        return answer
    except requests.exceptions.RequestException as e:
        return f"Error communicating with AI API: {e}"
    except json.JSONDecodeError:
        return "Error decoding JSON response from AI API."

def main():
    # Ask the user for configuration values.
    prompt_prefix, api_key, base_url, model_name, ai_name = get_terminal_inputs()

    # Loop until the user decides to stop.
    while True:
        command = input("Type 'screenshot' to capture a screenshot or 'stop' to exit: ").strip().lower()
        if command == "stop":
            print("Exiting program.")
            break
        elif command == "screenshot":
            screenshot = capture_screenshot_with_region()
            print("Sending prompt and image to AI model...")
            answer = get_ai_answer(api_key, base_url, model_name, prompt_prefix, screenshot)
            print("\n--- AI Response ---")
            print(answer)
            print("\n-------------------")
        else:
            print("Invalid command. Please type 'screenshot' or 'stop'.")

if __name__ == "__main__":
    main()
