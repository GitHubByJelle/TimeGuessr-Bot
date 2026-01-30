# TimeGuessr Bot
This project is a personal challenge I worked on in my free time to learn and experiment with new technologies. It allows me to explore tools and concepts such as Microsoft Teams webhooks (via Power Automate), Azure Bicep, Azure containerized cron jobs, and more advanced Playwright automation tasks.

[TimeGuessr](https://timeguessr.com/) is a guessing game where you try to determine both when and where a photo was taken. You’re shown a historical or vintage image and must guess the year and the location on a map. Visual clues like clothing, vehicles, architecture, signs, technology, and photo quality help you make an educated guess. The closer your answers are to the correct year and place, the more points you earn. It’s similar to GeoGuessr, but with an added time dimension.

My colleagues and I share our daily TimeGuessr scores in a Microsoft Teams channel. Because the difficulty varies each day, the score distribution changes as well. To make these scores more meaningful, I wanted a consistent, automatic benchmark.

To achieve this, I built a bot powered by an LLM (GPT-5.2) that plays TimeGuessr autonomously. The bot runs in our Azure environment and submits its score to the Teams channel every day at roughly the same time, providing a daily benchmark against which we can compare our own results.

<p align="center" width="100%">
    <img src="images\timeguessr-bot.gif" alt="A Perfect Bot playing the game" width="70%">
</p>

# Implementation Details

The project is written in Python and uses the dependencies defined in `pyproject.toml`. The most important libraries are:

* Playwright 
* OpenAI

The entire solution runs on Azure. The application is packaged as a Docker image and deployed to Azure Container Registry (ACR). From there, it is executed using Azure Container Jobs on a scheduled basis (cron). Runtime logs and diagnostics are collected and visualized through Application Insights. Results are posted to Microsoft Teams via a webhook created with Power Automate.

For the guessing logic, the bot uses Azure AI Foundry with an LLM (GPT-5.2) to predict the year and location of each image using structured outputs. These location predictions are then converted into geographic coordinates using Azure Maps Search.

The entire codebase is written asynchronously, allowing multiple bots to run in parallel on a single thread in a scalable and efficient way.

Instructions for installing and running the bot yourself, including prerequisites, can be found in [install.md](install.md). Please note, using this may come with (small) costs.

# How to use
This project uses [uv](https://astral.sh/) as the package manager. Begin by installing the required dependencies:
```bash
uv sync
```

Next, simply run main.py to run the bot.
```bash
uv run -m src.main.py
```

Here’s a clearer and more professional rephrasing of the disclaimer, while keeping the tone responsible and transparent:

# Disclaimer

This project is a personal, educational experiment. It is not intended to give players a competitive advantage on TimeGuessr or any other platform. Please use it responsibly.

The client component included in this repository interacts directly with timeguessr.com to play the game. If the owners of timeguessr.com object to this usage at any time, the client functionality will be promptly removed or disabled.

By using this code, you acknowledge that you are responsible for ensuring your usage complies with timeguessr.com’s terms of service and all applicable laws and regulations. The author does not endorse or support the use of this project to bypass fair play, gain unfair advantages, or infringe upon the rights of third parties.
