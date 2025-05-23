# Mosenergosbyt Meter Data Automation Script

This Python script automates the process of fetching meter data from the Saures API and submitting it to Mosenergosbyt. It also sends notifications via Telegram about the success or failure of the operations.

## Overview

The script performs the following tasks:
- Authenticates with the Saures API to retrieve meter data.
- Extracts electricity values from the response.
- Authenticates with the Mosenergosbyt API.
- Submits the meter data for calculation and saving.
- Sends notifications to specified Telegram chat IDs with the results or error messages.

## Features
- **Structured Code**: Organized into functions for better readability and maintainability.
- **Error Handling**: Comprehensive error handling with detailed logging.
- **Telegram Notifications**: Sends success or failure notifications to multiple Telegram chats.
- **Environment Variables**: Configuration via `.env` file for secure credential management.

## Requirements
- Python 3.11 or higher
- Required libraries: `requests`, `python-dotenv`

## Installation

1. **Clone the Repository** (if applicable):

- git clone `<repository-url>`.
- cd `<repository-directory>`.

2. **Create a Virtual Environment**:
- Check if `python3.*-venv` installed.
		
		dpkg -l | grep python.*venv

- If not - install it.

		apt install python3.11-venv

- Navigate to your project directory and create a virtual environment using the `venv` module. This will create a folder named `.venv` (or any name you choose) with an isolated Python environment:

		python3 -m venv .venv

3. **Activate the Virtual Environment**:
- Before installing packages or running the script, activate the virtual environment. This ensures that `python` and `pip` commands use the isolated environment instead of the system-wide installation:

		source .venv/bin/activate

3. **Install Dependencies**:
- Install pip if needed

		apt install python3-pip

- Install the required Python packages using `pip`: 

		.venv/bin/python -m pip install -r requirements.txt

4 **Set Up Environment Variables**:
- Copy a `.example.env` file in the same directory as the script to `.env`:
- Replace the placeholders with your actual credentials and configuration.

## Configuration

### Telegram Bot Setup
1. **Create a Telegram Bot**:
- Open Telegram and search for `@BotFather`.
- Start a chat with BotFather and send `/newbot`.
- Follow the instructions to set a name and username for your bot.
- Save the `TELEGRAM_BOT_TOKEN` provided by BotFather.

2. **Get Chat IDs for Notifications**:
- Start a chat with your bot by searching for its username and sending `/start`.
- To get your `chat_id`, use a bot like `@userinfobot` or make an API request:
  ```
  curl -X GET 'https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates'
  ```
  Replace `<YOUR_TOKEN>` with your bot token and find the `chat_id` in the response.
- If sending to multiple chats or groups, add the bot to each chat/group, send `/start`, and get each `chat_id`. List them in `TELEGRAM_CHAT_ID` separated by commas (e.g., `123456789,987654321`).

3. **Add Environment Variables**:
- Update the `.env` file with the `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` values.

### API Credentials
- Ensure you have valid credentials for both Saures and Mosenergosbyt APIs.
- Store sensitive information (logins, passwords, API URLs) in the `.env` file to keep them secure.

## Usage

Run the script using Python:

		python autometer.py


- The script will log its progress to `$LOG_FILE` (configurable in the `.env`).
- Notifications about success or failure will be sent to the specified Telegram chat IDs.

## Output
- **Success Notification Example** (sent to Telegram):

		✅ Mosenergosbyt Operation Success

		По введенным Вами показаниям (1000, 500) сумма начислений составит 1 500,00 руб.
		Показания успешно переданы

- **Failure Notification Example** (sent to Telegram):
		
		❌ Mosenergosbyt Operation Failure

		Error: Operation failed. Check logs for details.


## Troubleshooting
- **No Telegram Notifications**:
- Ensure `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are correctly set in the `.env` file.
- Verify that the recipients have started a chat with the bot by sending `/start`.
- Check internet connectivity and Telegram API availability.
- **API Authentication Errors**:
- Verify that the credentials (`LOGIN`, `SAURES_PASS`, `MOSENERGO_PASS`) in `.env` are correct.
- Check if the API URLs (`SAURES_API_URL`, `MOSENERGO_LK_URL`) are accessible and correct.
- **Logs for Debugging**:
- Review the log file (`$LOG_FILE`) for detailed error messages.

## Scheduling with Cron

To automate the execution of this script on the 23rd of every month at 12:00 PM (noon), you can use `cron`, a time-based job scheduler in Unix-like operating systems (Linux, macOS). Follow these steps to set up a cron job:

### Prerequisites
- Access to a Unix-like system with `cron` installed (most Linux distributions and macOS have it by default).

### Steps to Set Up Cron Job
1. **Open the Cron Job Editor**:
- Run the following command in your terminal to edit the cron jobs for the current user:
		
		crontab -e

2. **Add the Cron Job**:
- Add the following line to the crontab file to schedule the script to run on the 23rd of every month at 12:00 PM:

		0 12 23 * * /path/to/.venv/bin/python /path/to/autometer.py

3. **Verify the Cron Job**:
- List your cron jobs to ensure the new job is added:

		crontab -l

## Contributing
If you have suggestions for improvements or bug fixes, feel free to open an issue or submit a pull request.

## License
This project is licensed under the Apache License 2.0 - see the [LICENSE](https://www.apache.org/licenses/LICENSE-2.0) for details (if applicable).
