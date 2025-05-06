# How to use media-tagger as a Langchain tool

`media-tagger` can be exposed as a Langchain tool.

1. Install `media-tagger` with `pip install media-tagging[all]` command.

2. Import tool with
```
from media_tagging import tools as media_tagging_tools
```

3. Initialize tool

```
media_tagging_tool = media_tagging_tools.MediaTaggingResults()
```

4. Add tool to any Langchain Agent or AgentExecutor.

```
from langchain import agents

agent = agents.create_tool_calling_agent(YOUR_LLM, [media_tagging_tool], YOUR_PROMPT)
```

5. Call an agent

```
import langchain_core

def _get_session_history(session_id):
  return SQLChatMessageHistory(session_id, 'sqlite:///memory.db')

agent_executor = langchain_core.runnables.history.RunnableWithMessageHistory(
  agents.AgentExecutor(agent=agent, tools=[media_tagging_tool]),
  _get_session_history,
  input_messages_key='input',
  history_messages_key='chat_history',
)

agent_executor.invoke(
  {'input': YOUR_QUESTION},
  config={'configurable': {'session_id': YOUR_SESSION_ID}},
)
```
