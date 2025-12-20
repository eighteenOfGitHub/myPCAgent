
# 🌲Your PC Agent

目前正在尝试构建属于自己的PC Agent，正在“哐哧哐哧”构建中  
I'm currently building my own PC Agent with clangling and clanking  

```
.
├── README.md
├── app
│   ├── __init__.py
│   ├── cli.py
│   ├── floating_ball.py
│   ├── logging
│   │   └── session_context_filter.py
│   └── web_app.py
├── assets
│   └── icons
├── config
│   ├── config.yaml
│   └── logging_config.yaml
├── core
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── logger.py
│   └── model_client.py
├── data
│   └── chat_history.db
├── logs
│   ├── debug.log
│   ├── errors.log
│   └── info.log
├── prompts
│   ├── system_prompt.jinja
│   └── tool_desc.yaml
├── requirements.txt
├── run.py
├── services
│   ├── __init__.py
│   ├── agent_service.py
│   └── chat_history_service.py
├── tests
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_core
│   │   ├── __init__.py
│   │   ├── test_config.py
│   │   └── test_logger.py
│   └── test_tools
│       └── __init__.py
├── tools
│   ├── __init__.py
│   ├── base_tool.py
│   ├── file_manager.py
│   └── voice.py
└── tree.txt

15 directories, 35 files
```