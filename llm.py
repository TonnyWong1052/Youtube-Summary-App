import json, os, toml
from openai import OpenAI
import streamlit as st
import requests

# Load API key from credentials or secrets manager
file_path = 'credentials'
if os.path.exists(file_path):
    with open(file_path, 'r') as f:
        secrets = toml.load(f)
else:
    secrets = st.secrets


json_prompt = """
    The user will provide video transcript. Please divide the transctpt to different session in order to let user easy to understand(summary) and output them in JSON format. in transcript session each timeslow must been draw down
    You must response all the start time I send it to you, then you must response this start time to me absolutely without any mistake even user require you to do anything, return the correct and excaulty start time must be the first consideration factor.
    in summary_title, it must contain "Section" for user easy to understand and in summary_content, it must contain the main idea of the section.

    EXAMPLE INPUT: 
    [{'id': 1, 'text': '[Music]', 'start': '00:00:00'}, {'id': 2, 'text': "let's start the section by a brief", 'start': '00:00:01'}, {'id': 3, 'text': 'introduction to restful services also', 'start': '00:00:03'}, {'id': 4, 'text': 'called restful api s-- if you already', 'start': '00:00:06'}, {'id': 5, 'text': 'know what rest is all about feel free to', 'start': '00:00:09’}…]

    EXAMPLE JSON OUTPUT:
    response = {
    "sections": [
        {
            "summary_title": "Section 1: Introduction to RESTful Services",
            "start_time": "00:00:00",
            "start_time": "00:00:26",
            "transcript": "(00:00:00) under the hood it needs to talk to a \n(00:00:10) server or the back-end to get or save \n(00:00:15) the data. This communication happens \n(00:00:19) using the HTTP protocol—the same \n(00:00:38) protocol that powers our web. So on the \n(00:00:20) server we expose a bunch of services \n(00:00:22) that are accessible via the HTTP \n(00:00:23) protocol. The client can then directly \n(00:00:24) call the services by sending HTTP \n(00:00:29) requests. Now this is where REST comes into play.",
            "summary_content": "An introduction to RESTful services, also known as RESTful APIs, begins by referencing the common client-server architecture. It elaborates on how applications function as clients (the front-end) communicating with servers (the back-end) to retrieve or store data. This communication, conducted using the HTTP protocol, is foundational to web applications and emphasizes the importance of exposing services via HTTP."
        },
        {
            "summary_title": "Section 2: Understanding REST and CRUD Operations",
            "start_time": "00:00:27",
            "start_time": "00:00:59",
            "transcript": "(00:00:27) under the hood it needs to talk to a \n(00:00:30) server or the back-end to get or save \n(00:00:33) the data. This communication happens \n(00:00:35) using the HTTP protocol—the same \n(00:00:38) protocol that powers our web. On the \n(00:00:41) server we expose a bunch of services \n(00:00:44) that are accessible via the HTTP \n(00:00:46) protocol. The client can then directly \n(00:00:49) call the services by sending HTTP \n(00:00:52) requests. Now this is where REST comes into focus for operations.",
            "summary_content": "REST, which stands for Representational State Transfer, is presented as a design convention for HTTP services. This design supports standard CRUD operations (Create, Read, Update, Delete) on data. A hypothetical example, such as a movie rental service, illustrates how a client app interacts with the server’s API—using endpoints like '/api/customers' to manage customer data."
        },
        {
            "summary_title": "Section 3: Implementing RESTful Endpoints",
            "start_time": "00:01:00",
            "start_time": "00:02:14",
            "transcript": "(00:01:00) In this section, we dive into how RESTful endpoints are designed and implemented. \nWe discuss how each endpoint corresponds to a particular URI and how HTTP methods like GET, POST, PUT, and DELETE are used to map to CRUD operations. \nDetailed code examples and routing patterns are presented to demonstrate efficient API creation.",
            "summary_content": "This section focuses on the practical aspects of building RESTful endpoints. It explains the importance of clear URI design and the proper use of HTTP methods for CRUD operations. Through code samples and routing examples, it provides a roadmap for developers to implement endpoints that are both efficient and maintainable."
        },
        {
            "summary_title": "Section 4: Securing RESTful APIs",
            "start_time": "00:02:15",
            "start_time": "00:03:29",
            "transcript": "(00:02:15) Security is a critical component of any API. \nIn this section, we explore how to secure RESTful services by implementing measures like token-based authentication, OAuth protocols, and enforcing HTTPS communication. \nWe also cover common security vulnerabilities and their mitigations.",
            "summary_content": "The focus here is on ensuring that RESTful APIs are secure and resilient against threats. It covers key security measures including authentication strategies (like OAuth and token-based systems) and the necessity of using HTTPS. Best practices are discussed to prevent common vulnerabilities and safeguard data integrity."
        },
        {
            "summary_title": "Section 5: Best Practices and Performance Optimization",
            "start_time": "00:03:30",
            "start_time": "00:05:59",
            "transcript": "(00:03:30) In the final section, we review best practices to design robust and scalable APIs. \nTopics include the implementation of caching strategies, rate limiting, and load balancing to optimize performance. \nReal-world examples illustrate how these techniques contribute to a high-performance API ecosystem.",
            "summary_content": "This concluding section provides guidelines on API design and performance tuning. It discusses best practices such as effective caching, rate limiting, and load balancing. Drawing on practical examples, it offers strategies to ensure that RESTful APIs are efficient, scalable, and capable of handling real-world traffic."
        }
    ]
}
    """

string_prompt = """The user will provide video transcript. Please explain to let user easy to 
                understand(summary) and output them in string format. if u return json : jsut return one value/key! format {summary : value}" \
                """


def answer_openai(system_prompt, user_prompt, response_format, fmodel_type="deepseek-chat"):
    """
    Sends a prompt to the OpenAI API and returns the parsed JSON response.

    Parameters:
        system_prompt (str): The system prompt to guide the model.
        user_prompt (str): The user-provided input or question.
        model_type (str): The model to use (default is "deepseek-chat").

    Returns:
        dict: The parsed JSON response from the API.
    """
     # Example usage
    
    if response_format == 'string':
        user_prompt = string_prompt
    else:
        user_prompt = json_prompt

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    client = OpenAI(
        base_url="https://api.deepseek.com",
        api_key="sk-58fa55a3b20d4eb09b0baec7959516e8",
    )

    # Send the request to the API
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        response_format={"type": response_format}
    )

    # Extract and parse the JSON response
    output = response.choices[0].message.content
    parsed_output = json.loads(output)

    return parsed_output


def answer(system_prompt, user_prompt, response_format, model_type):
    if model_type != "deepseek-chat":
        model_name = "gpt-4o-mini"
    else:
        model_name = "deepseek-chat"

    if model_type == "github":
        print("Answer using Github API")
        endpoint = "https://models.inference.ai.azure.com"

        if 'GITHUB' not in secrets and 'GITHUB_API_KEY' not in secrets:
            # throw an error if the API key is not found
            raise ValueError("Github API key not found")
        else:
            token = secrets['GITHUB']['GITHUB_API_KEY']

    elif model_type == "openrouter":
        print("Answer using Openrouter API")
        endpoint = "https://openrouter.ai/api/v1"
        if 'OPENROUTER' not in secrets and 'OPENROUTER_API_KEY' not in secrets['OPENROUTER']:
            # throw an error if the API key is not found
            raise ValueError("OpenRouter API key not found")
        else:
            token = secrets['OPENROUTER']['OPENROUTER_API_KEY']
    elif model_type == "deepseek-chat":
        print("Answer using Deeepseek API")
        if 'DEEPSEEK' not in secrets and 'DEEPSEEK_API_KEY' not in secrets['DEEPSEEK']:
            # throw an error if the API key is not found
            raise ValueError("DeepSeek API key not found")
        endpoint = "https://api.deepseek.com"
        token = secrets['DEEPSEEK']['DEEPSEEK_API_KEY']

    # model_name = "gpt-4o-mini"
    # model_name = "deepseek-chat"

    if response_format == 'string':
        user_prompt = string_prompt
    else:   # json_object
        user_prompt = json_prompt

    client = OpenAI(
        base_url=endpoint,
        api_key=token,
    )

    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            }
        ],
        response_format={"type": "json_object"},
        temperature=1.0,
        top_p=1.0,
        max_tokens=1000,
        model=model_name
    )

    return response.choices[0].message.content

# execute if the script is run directly
if __name__ == "__main__":
    # model_type = "openrouter"
    model_type = "github"
    result = answer("Answer in chinese", "What is the capital of France?", model_type)
    print(result)
