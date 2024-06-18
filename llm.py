"""Autogen Agent Setup and Inference.

Usage
-----
crawler = AutoGenCrawler()
...
# long-running sync operation
result: Chat = crawler.run(prompt, start_url)
"""

import os
from threading import Thread, Event
import time
from typing import Any, Dict, List, Optional
import autogen
from autogen import ChatResult
import instructor
import sys
from openai import OpenAI

# append parent directory to PATH to import own modules
sys.path.append(os.path.dirname(os.path.abspath(os.getcwd())))

from services.config import (
    ANALYST_SYSTEM_MESSAGE,
    CODER_SYSTEM_MESSAGE,
    COORDINATOR_SYSTEM_MESSAGE,
    EXECUTOR_SYSTEM_MESSAGE,
    start_message
)
from services.browser import open_browser_session
from models.chat import Chat

class AutoGenCrawler:

    def __init__(
        self,
        base_model: str | None = None,
        execution_config: Dict[str, Any] | None = None,
        summary_method: str | None = None,
        max_round: int = 50
    ) -> None:
        """Setup on creating an instance."""

        self.base_model: str = base_model or "gpt-3.5-turbo-0125" # "gpt-4o-2024-05-13"
        self.execution_config: Dict[str, Any] | None = execution_config
        if not execution_config:
            self.execution_config: Dict[str, Any] = {
                "last_n_messages": 3,
                "work_dir": "web",
                "use_docker": False,
            }
        self.summary_method: str = summary_method or "reflection_with_llm"
        self.max_round: int = max_round
        self.exceptions_per_crawl: int = 0

        ### OpenAI instance ###
        self.oai_client: OpenAI = instructor.patch(OpenAI(), mode=instructor.Mode.JSON)

        ### Browser Thread Setup ###
        self.trigger_crawl_start_event: Event = Event()
        self.trigger_thread_stop_event: Event = Event()
        self.start_url: str | None = None
        self.browser_thread: Thread | None = None

        ### AutoGen Agent configuration ###
        self._llm_config_list: List[Dict[str, str]] = [
            {
                "model": self.base_model,
                "api_key": os.environ.get("OPENAI_API_KEY")
            }
        ]
        self.autogen_llm_config: Dict[str, Any] = {
            "timeout": 600,
            "cache_seed": None,
            "config_list": self._llm_config_list,
            "temperature": 0.2,
        }
        self._initialize_agents()
        self.groupchat = autogen.GroupChat(
            agents=[self.coordinator, self.coder, self.executor, self.analyst],
            messages=[],
            max_round=self.max_round,
            speaker_selection_method=self.state_transition,
        )
        self.manager = autogen.GroupChatManager(
            groupchat=self.groupchat,
            llm_config=self.autogen_llm_config
        )


    def _initialize_agents(self) -> None:
        """Setup all agents that are needed.
        
        Coder
        -----
        Writes Code that performs an action on the current browser page

        Executor
        --------
        Extract and executes generated code from previous messages.

        Analyst
        -------
        Analyzes html content of a url and extracts all interaction elements found on that page.

        Coordinator
        -----------
        Defines the task for the coder and decides on the overall outcome of the run.
        """
        self.coder = autogen.ConversableAgent(
            system_message=CODER_SYSTEM_MESSAGE,
            name="Coder",
            llm_config=self.autogen_llm_config,
        )
        self.executor = autogen.UserProxyAgent(
            name="Executor",
            human_input_mode="NEVER",
            code_execution_config=self.execution_config,
            llm_config=self.autogen_llm_config,
            system_message=EXECUTOR_SYSTEM_MESSAGE
        )
        self.analyst = autogen.ConversableAgent(
            name="Analyst",
            system_message=ANALYST_SYSTEM_MESSAGE,
            llm_config=self.autogen_llm_config,
            human_input_mode="NEVER"
        )
        self.coordinator = autogen.ConversableAgent(
            name="Coordinator",
            llm_config=self.autogen_llm_config,
            human_input_mode="NEVER"
        )


    def _reset_agents(self) -> None:
        """Reset agents each run to prevent information flow between runs if not wanted."""
        self.coder.reset()
        self.executor.reset()
        self.analyst.reset()
        self.coordinator.reset()
        self.groupchat.reset()
        self.manager.reset()


    def state_transition(self, last_speaker, groupchat) -> autogen.ConversableAgent | None:
        messages = groupchat.messages

        if last_speaker is self.manager:
            return self.coordinator
        elif last_speaker is self.coder:
            return self.executor
        elif last_speaker is self.executor:
            return self.analyst
        elif last_speaker is self.analyst:
            if "Exitcode: 1" in messages[-1]["content"]:
                self.exceptions_per_crawl += 1
            if self.exceptions_per_crawl == 5:
                return None
            return self.coordinator
        elif last_speaker is self.coordinator:
            if "MAIN GOAL ACHIEVED" in messages[-1]["content"] or "MAIN GOAL NOT ACHIEVED" in messages[-1]["content"]:
                return None
            return self.coder
        else: return None


    def start_browser(self, start_url) -> bool:
        """Resets all event triggers and starts a new browser instance."""
        # clear events
        if self.browser_thread is None:
            self.trigger_thread_stop_event.clear()
            self.trigger_crawl_start_event.clear()
            self.browser_thread = Thread(
                target=open_browser_session,
                args=(start_url, self.trigger_crawl_start_event, self.trigger_thread_stop_event,)
            )
            self.browser_thread.start()
            return True
        return False


    def stop_browser(self, auto_stop: bool) -> None:
        """Clears all event triggers and stops all browser instances."""
    
        # Run is finished, thread and browser can be closed by setting this event
        if auto_stop is True:
            self.trigger_thread_stop_event.set()
            self.browser_thread.join()
            self.browser_thread = None
            self.trigger_thread_stop_event.clear()
            self.trigger_crawl_start_event.clear()


    def get_nr_code_errors(chat_history):
        errors = 0
        for message in chat_history:
            if 'name' in message and  message['name'] == "Executor" and "exitcode: 1" in message['content']:
                errors += 1
        return errors
    

    def get_nr_generated_scripts(chat_history):
        scripts = 0
        for message in chat_history:
            if 'name' in message and  message['name'] == "Coder" and "```python" in message['content']:
                scripts += 1
        return scripts


    def run(
        self,
        prompt: str,
        start_url: str | None = None,
        auto_stop: bool = True
    ) -> Optional[Chat]:
        """Perform a series of tasks that fulfil the goal described in the prompt.

        Parameters
        ----------
        prompt: str, the main task that needs to be solved by the agents
        start_url: str | None, the start url from where the crawl should start
        auto_stop: bool, indicates whether the browser instance should be closed automatically after crawl finish

        Returns
        -------
        chat_result: Chat | None, a Chat model containing all information or None if no connection was established
        """
        self.exceptions_per_crawl = 0
        is_browser_started: bool = self.start_browser(start_url)
        # if a browser session is running, then set the start url to None
        if not is_browser_started:
            start_url = None
        self.coordinator.update_system_message(COORDINATOR_SYSTEM_MESSAGE(prompt, start_url))

        # Wait for the page content to be initialized and loaded before starting the crawling
        is_page_loaded: bool = self.trigger_crawl_start_event.wait(timeout=30)
        if not is_page_loaded:
            print("ERROR: Page loading too long, aborting...")
            return None

        start_time: float = time.time()
        # TOKEN CONSUMPTION STARTS HERE
        chat_result: ChatResult = self.coordinator.initiate_chat(
            self.manager,
            message=start_message(prompt, start_url),
            summary_method=self.summary_method,
        )
        end_time: float = time.time()
        duration: float = end_time - start_time

        self.stop_browser(auto_stop)
        
        if auto_stop:
            # to completely avoid any information or metric flow between runs
            self._reset_agents()


        result: Chat = Chat(
            history=chat_result.chat_history,
            duration=duration,
            nr_tokens=chat_result.cost["usage_excluding_cached_inference"][self.base_model]["total_tokens"],
            interactions=len(chat_result.chat_history),
            nr_generated_scripts=AutoGenCrawler.get_nr_generated_scripts(chat_result.chat_history),
            nr_code_errors=AutoGenCrawler.get_nr_code_errors(chat_result.chat_history),
            summary=chat_result.summary,
            gherkin=True if("GIVEN" in prompt or "WHEN" in prompt or "THEN" in prompt) else False
        )

        return result


if __name__ == "__main__":
    example_input: str = """Given this is the current URL: "http://localhost:8080/owners/find"
When I search for an owner with the last name "Franklin"
Then "George Franklin" can be seen as an owner"""
    start_url: str = "http://localhost:8080/owners/find"

    crawler: AutoGenCrawler = AutoGenCrawler()
    result: Chat = crawler.run(example_input, start_url)
    statistics = f"Statistics:\n  Interactions: {result.interactions}\n  Number of tokens: {result.nr_tokens}\n  Duration: {result.duration:.2f} seconds\n  Generated code scripts: {result.nr_generated_scripts}\n  Code errors: {result.nr_code_errors}\n  Summary: " + result.summary + "\n"
    print(statistics)