# Nice LLM but can it run Gherkin? Experiments on test scenario execution with Language Models

This is the online appendix for a paper submitted to the [A-Test workshop](https://a-test.org/).
 
## Abstract

Gherkin serves as a structured language for defining software behaviors in natural language, particularly valuable in the context of automated testing. With recent advancements in natural language processing, including the emergence of Large Language Models (LLMs), there is growing potential to leverage such linguistic definitions for automated testing purposes. This paper investigates the feasibility and effectiveness of employing LLMs to execute Gherkin test scripts for web application testing, utilizing the AutoGen framework for orchestration and coordination. Our preliminary findings suggest that our LLM agent system has the potential to automate test scenarios. We found high success rates for executing simple as well as more complex test scenarios but observed existing hurdles regarding fault detection.

## Repo Content

### 1. `Experiment_Results.xlsx`

This Excel file contains the exact scenarios with detailed information and metrics about every run conducted in the context of the experiments. The metrics include:

- Reported success: Reported by the LLM agents
- Manually checked success: if the scenario did execute correctly
- Matching success: Do "Reported success" and "Manually checked success" match
- Number of turns: Interactions with an LLM agent
- Execution time (in seconds)
- Consumed tokens (according to the AutoGen framework)
- Code exceptions: from executing generated code
- Scripts generated: by the LLM coder
- Test aborted (for negative tests): the LLM agents correctly recognized they could not fulfill the testing goal

### 2. `Experiment_Runs`

This folder contains two subfolders which store the executed runs in the form of JSON files. The subfolders are:

- `GPT3_5`: Contains JSON files for runs executed using the GPT-3.5 Turbo model.
- `GPT4o`: Contains JSON files for runs executed using the GPT-4o model.

### 3. Service scripts

#### a. `config.py`

This Python file includes the system prompts for the included agents: Coordinator, Coder, Executor, and Analyst. Additionally, it contains the start message for initiating the experiments.

#### b. `browser.py`

This Python file includes a function to reuse an already open browser instance as needed during the experiments.

#### c. `llm.py`

This Python file includes the `AutoGenCrawler` class which is responsible for handling the agents. Its functionalities include:

- Initializing the agents
- Resetting the agents
- Choosing the next agent to speak
- Starting and stopping the browser

Moreover, a `run` function is included, triggering the initiation of the chat when called, aiming to achieve the goal specified in the prompt. `llm.py` is an executable script that will start an example Gherkin test, looking for an owner in the PetClinic application.

**Note**: There are two prerequisites for running `llm.py`:
1. The `OPENAI_API_KEY` environment variable needs to be set to a valid OpenAI API key.
2. The PetClinic Application must be running on `localhost:8080`.

Running
   ```bash
    python .\llm.py
   ```
will start the experiment process and log the chat messages in the console followed by a short summary of the run. The default model utilized is GPT-3.5 Turbo.
