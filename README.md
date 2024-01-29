# TIC TON APP

## Setup

1. Install [poetry](https://python-poetry.org/docs/) on our device 

    take macOS as example

    ```bash
    brew install poetry
    ```

2. Install dependencies

    ```bash
    poetry install
    ```

3. Create `.env` file and complete

    - get `TICTON_TG_BOT_TOKEN` from [Bot Father](https://telegram.me/BotFather)

    ```bash
    cp .env.example .env
    ```

4. Start mongodb 

    ```bash
    docker compose up -d
    ```

5. Start your virtual enviroments

    ```bash
    poetry shell
    ```

6. Initialize your database

    ```bash
    poetry run python3 main.py init
    ```

7. Start your app

    ```bash
    poetry run python3 main.py start
    ```