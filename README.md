# First Experiments on Automated Execution of Gherkin Test Specifications with Collaborating LLM Agents

This is the online appendix for a paper submitted to the [A-Test workshop](https://a-test.org/).
 
## Abstract

Gherkin is a domain-specific language for describing test scenarios in natural language, which are the basis for automated acceptance testing. The emergence of Large Language Models (LLMs) has opened up new possibilities for processing such test specifications and for generating executable test code. This paper investigates the feasibility of employing LLMs to execute Gherkin test specifications utilizing the AutoGen multi-agent framework. Our findings show that our LLM agent system is able to automatically run the given test scenarios by autonomously exploring the system under test, generating executable test code on the fly, and evaluating execution results. We observed high success rates for executing simple as well as more complex test scenarios, but we also identified difficulties regarding failure scenarios and fault detection.

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
