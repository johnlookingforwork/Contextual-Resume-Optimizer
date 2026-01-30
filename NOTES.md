## What is Pydantic?

Pydantic is a library for Python that performs data validation and settings management using Python type hints.

While Python is normally "dynamically typed" (meaning variables can change from a string to a number whenever they want), Pydantic forces your data to conform to a specific "Schema".

Why it matters:
System Reliability: One of the biggest challenges in AI applications is "Data Drift"—when an AI model returns a response in a format you didn't expect. Pydantic acts as a Guardrail, ensuring that the AI's output matches your application's internal logic.
Documentation: Defining data schemas allows others to immediately understand the structure of the data at a glance.

## What is Ollama?

Ollama is an open-source framework designed to run Large Language Models (LLMs) locally on your own machine. It simplifies the process of downloading, managing, and interacting with powerful models—like Llama 3.2—without needing to rely on external cloud providers or complex setups.

Think of it as the "engine" that hosts the model, providing a bridge between your code and the AI's reasoning capabilities.

Why it matters:
Local Processing & Privacy: Since the model runs on your hardware, sensitive data like resumes never leave your local environment. This is critical for maintaining data privacy and security.

Seamless Integration: Ollama provides a local API endpoint. This allows you to send raw text (like your extracted resume data) to the model and receive a generated response that you can then pipe directly into a Pydantic schema for validation.

Resource Efficiency: It is highly optimized to run on consumer-grade hardware (like Mac, Linux, or Windows), making it possible to build and test sophisticated AI applications without expensive server costs.
