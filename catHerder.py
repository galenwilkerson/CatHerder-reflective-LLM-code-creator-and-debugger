"""
Author: Galen Wilkerson
Date: 2024-08-06
Description: 
CatHerder is a simple and intuitive code creator and debugger that utilizes Large Language Model (LLM) reflection to help you debug Python code effectively. By iteratively refining code with the assistance of an LLM, this tool aims to make the debugging process smoother and more efficient.

You can also use it to gradually add features to existing code. This is where the cat herding really begins...
"""

import openai
import os
import argparse


def read_api_key(file_path):
    """
    Reads the API key from a specified file.

    Parameters:
    file_path (str): The path to the file containing the API key.

    Returns:
    str: The API key.
    """
    with open(file_path, 'r') as file:
        return file.read().strip()

def extract_code(response, code_type='python'):
    """
    Extracts the code from the OpenAI API response based on the specified type.

    Parameters:
    response (dict): The response dictionary from the OpenAI API.
    code_type (str): The type of code block (default is 'python').

    Returns:
    str: The extracted code.
    """
    # Extract the message content
    content = response['choices'][0]['message']['content']

    # Find the start and end of the code block
    start_tag = f"```{code_type}\n"
    start_index = content.find(start_tag) + len(start_tag)
    end_index = content.find("\n```", start_index)

    # Extract the code
    code = content[start_index:end_index]
    
    return code

def call_chatgpt(prompt, client, code_type='python', special_instructions='Implement a script in a single code block to perform this task: '):
    """
    Calls the OpenAI API to generate code based on the provided prompt.

    Parameters:
    prompt (str): The prompt describing the desired code.
    client (openai.OpenAI): The OpenAI client.
    code_type (str): The type of code block (default is 'python').

    Returns:
    str: The generated code.
    """
    special_instructions = f"Implement a {code_type} script in a single code block to perform this task: "
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": special_instructions + prompt}
        ]
    )
    # print(response)  # Add this line to inspect the response structure
    return extract_code(response.dict(), code_type=code_type)

def debug_code_with_chatgpt(original_prompt, code, error, client, code_type='python'):
    """
    Calls the OpenAI API to debug the provided code based on the encountered error.

    Parameters:
    original_prompt (str): The original prompt describing the desired code.
    code (str): The code that produced an error.
    error (str): The error message.
    client (openai.OpenAI): The OpenAI client.
    code_type (str): The type of code block (default is 'python').

    Returns:
    str: The suggested fix for the code.
    """
    prompt = f"The original prompt was:\n\n{original_prompt}\n\nHere is the code:\n\n{code}\n\nIt produced the following error:\n\n{error}\n\nPlease help me fix it."
    return call_chatgpt(prompt, client, code_type=code_type)

def save_code_to_file(code, code_type, iteration, status):
    """
    Saves the provided code to a specified file.

    Parameters:
    code (str): The code to be saved.
    code_type (str): The type of code (e.g., python, latex, html).
    iteration (int): The iteration number of the code.
    status (str): The status of the code (e.g., iteration number or 'debugged').
    """
    # Ensure the scripts directory exists
    if not os.path.exists('./scripts'):
        os.makedirs('./scripts')

    # Determine the file extension based on the code type
    ext = 'py' if code_type == 'python' else code_type

    file_path = f"./scripts/script_{status}.{ext}"
    with open(file_path, 'w') as file:
        file.write(code)

def main():
    """
    Main function to read API key, generate code, and debug it iteratively.
    """
    parser = argparse.ArgumentParser(description='CatHerder: Reflective LLM Debugger')
    parser.add_argument('-p', '--prompt', type=str, help='The code prompt to generate new code or the path to a file containing the prompt', required=False)
    parser.add_argument('-m', '--modify', type=str, help='The path to the existing code file to modify', required=False)
    parser.add_argument('-c', '--code_type', type=str, default='python', help='The type of code (default: python, latex, html, etc.)')
    parser.add_argument('-i', '--iterations', type=int, default=5, help='Number of debug iterations to perform (default: 5)')
    args = parser.parse_args()

    if not args.prompt and not args.modify:
        parser.print_usage()
        print("\nUsage Information:")
        print("  -p, --prompt: The code prompt to generate new code or the path to a file containing the prompt.")
        print("  -m, --modify: The path to the existing code file to modify.")
        print("  -c, --code_type: The type of code (default: python, latex, html, etc.). Default is 'python'.")
        print("  -i, --iterations: Number of debug iterations to perform. Default is 5.")
        print("\nEither a prompt or a path to modify an existing code file must be provided.")
        return

    api_key = read_api_key('api_key.txt')
    openai.api_key = api_key
    client = openai

    if args.prompt:
        if os.path.isfile(args.prompt):
            with open(args.prompt, 'r') as file:
                prompt = file.read()
        else:
            prompt = args.prompt
        code = call_chatgpt(prompt, client, args.code_type)
    elif args.modify:
        with open(args.modify, 'r') as file:
            code = file.read()
        prompt = input("Please describe the modifications you want to make: ")
        code = call_chatgpt(prompt, client, args.code_type, special_instructions='Modify the following code:\n\n' + code + '\n\n')

    if args.code_type == 'latex':
        save_code_to_file(code, args.code_type, 0, 'initial')
        print(f"Code saved to ./scripts/script_initial.{args.code_type}")
        return

    print('------------------')
    print("Initial code generated by ChatGPT:\n", code)
    print('------------------')

    save_code_to_file(code, args.code_type, 0, 'initial')

    last_error_message = None

    for i in range(1, args.iterations + 1):
        print(f"\nIteration {i}:")

        try:
            if args.code_type == 'python':
                exec(code)
            else:
                print("Execution not supported for this code type in the current implementation.")
                break
            print("Code executed successfully.")
            save_code_to_file(code, args.code_type, i, 'debugged')
            print(f'Saved to ./scripts/script_debugged.{args.code_type}')
            break
        except Exception as e:
            error_message = str(e)
            print("Error encountered:", error_message)

            if error_message == last_error_message:
                print("Encountered the same error. Stopping iterations.")
                break
            last_error_message = error_message
            
            # Get help from ChatGPT
            code = debug_code_with_chatgpt(args.prompt, code, error_message, client, args.code_type)
            print('------------------')
            print("ChatGPT suggests the following fix:\n", code)
            print('------------------')

            save_code_to_file(code, args.code_type, i, f'iteration_{i}')

    # Save the last version of the code
    save_code_to_file(code, args.code_type, args.iterations, f'final')
    # Determine the file extension based on the code type
    ext = 'py' if args.code_type == 'python' else args.code_type
    print(f"Final version saved to ./scripts/script_final.{ext}")

if __name__ == "__main__":
    main()


