import json
import requests
import sys
import logging
import os
from datetime import datetime
from dotenv import load_dotenv


def setup_environment() -> dict[str, str]:
    """Load environment variables and validate their presence.
    
    Returns:
        dict[str, str]: Dictionary with required environment variables.
    
    Raises:
        SystemExit: If any required environment variable is missing.
    """
    load_dotenv()
    required_env_vars: list[str] = [
        'LOGIN',
        'LOG_FILE',
        'SAURES_PASS',
        'SAURES_API_URL',
        'METER_ID',
        'MOSENERGO_LK_URL',
        'MOSENERGO_PASS',
        'TELEGRAM_BOT_TOKEN',
        'TELEGRAM_CHAT_ID',
    ]
    missing_vars: list[str] = [var for var in required_env_vars if not os.environ.get(var)]
    if missing_vars:
        logging.error('Missing environment variables: %s', ', '.join(missing_vars))
        sys.exit(1)
    
    return {
        'login': os.environ.get('LOGIN', ''),
        'log_file': os.environ.get('LOG_FILE', ''),
        'saures_pass': os.environ.get('SAURES_PASS', ''),
        'saures_api_url': os.environ.get('SAURES_API_URL', ''),
        'meter_id': os.environ.get('METER_ID', ''),
        'mosenergo_lk_url': os.environ.get('MOSENERGO_LK_URL', ''),
        'mosenergo_pass': os.environ.get('MOSENERGO_PASS', ''),
        'telegram_bot_token': os.environ.get('TELEGRAM_BOT_TOKEN', ''),
        'telegram_chat_id': os.environ.get('TELEGRAM_CHAT_ID', ''),
    }


def setup_logging(log_file_path: str = '/var/log/autometer.log') -> None:
    """Configure logging with the specified log file path.
    
    Args:
        log_file_path (str): Path to the log file. Defaults to '/var/log/autometer.log'.
    """
    logging.basicConfig(
        filename=log_file_path,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def send_telegram_message(token: str, chat_id: str, text: str) -> bool:
    """Send a message via Telegram Bot API.
    
    Args:
        token (str): Telegram Bot API token.
        chat_id (str): Chat ID of the recipient.
        text (str): Message text to send.
    
    Returns:
        bool: True if message was sent successfully, False otherwise.
    """
    url: str = f"https://api.telegram.org/bot{token}/sendMessage"
    payload: dict[str, str] = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown'
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        result: dict = response.json()
        if result.get('ok'):
            logging.info('Telegram message sent successfully to chat_id %s', chat_id)
            return True
        else:
            logging.error('Failed to send Telegram message: %s', result.get('description', 'Unknown error'))
            return False
    except requests.exceptions.RequestException as e:
        logging.error('Error sending Telegram message: %s', str(e))
        return False


def authenticate_saures(api_url: str, login: str, password: str) -> str:
    """Authenticate with Saures API and retrieve session ID.
    
    Args:
        api_url (str): Base URL of the Saures API.
        login (str): User login for authentication.
        password (str): User password for authentication.
    
    Returns:
        str: Session ID (sid) if authentication is successful.
    
    Raises:
        SystemExit: If authentication fails or an error occurs.
    """
    saures_login_url: str = f'{api_url}/login'
    headers: dict[str, str] = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'
    }
    data: dict[str, str] = {
        'email': login,
        'password': password
    }

    logging.info('Connecting to Saures API for authentication')
    try:
        response = requests.post(saures_login_url, headers=headers, data=data)
        response.raise_for_status()
        result: dict = response.json()
        if result.get('status') == 'ok':
            return result['data']['sid']
        else:
            logging.error('Authentication error: %s', result.get('errors', []))
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        logging.error('Request to Saures API failed: %s', str(e))
        sys.exit(1)
    except (ValueError, KeyError) as e:
        logging.error('Error processing Saures API response: %s', str(e))
        sys.exit(1)


def fetch_saures_meter_data(api_url: str, sid: str, meter_id: str, current_time: str) -> dict:
    """Fetch meter data from Saures API.
    
    Args:
        api_url (str): Base URL of the Saures API.
        sid (str): Session ID for authentication.
        meter_id (str): ID of the meter to fetch data for.
        current_time (str): Current timestamp in format 'YYYY-MM-DDThh:mm:ss'.
    
    Returns:
        dict: Meter data if request is successful.
    
    Raises:
        SystemExit: If request fails or response is invalid.
    """
    saures_meters_url: str = f'{api_url}/object/meters?sid={sid}&id={meter_id}&date={current_time}'
    logging.info('Fetching meter data from Saures API')
    try:
        response = requests.get(saures_meters_url)
        response.raise_for_status()
        result: dict = response.json()
        if result.get('status') == 'ok':
            logging.info('Successfully retrieved meter data from Saures')
            return result['data']
        else:
            logging.error('Failed to fetch meter data: %s', result.get('errors', []))
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        logging.error('Request to fetch meter data failed: %s', str(e))
        sys.exit(1)
    except (ValueError, KeyError) as e:
        logging.error('Error processing meter data response: %s', str(e))
        sys.exit(1)


def get_electricity_vals(data: dict) -> list[float]:
    """Extract electricity meter values from Saures API response.
    
    Args:
        data (dict): Response data from Saures API.
    
    Returns:
        list[float]: List of rounded electricity values or empty list if not found.
    """
    for sensor in data.get('sensors', []):
        for meter in sensor.get('meters', []):
            if meter.get('type', {}).get('name') == 'Электричество':
                return [round(val) for val in meter.get('vals', [])]
    return []


def authenticate_mosenergo(lk_url: str, login: str, password: str) -> tuple[str, requests.Session]:
    """Authenticate with Mosenergosbyt API and retrieve session ID.
    
    Args:
        lk_url (str): Base URL of the Mosenergosbyt API.
        login (str): User login for authentication.
        password (str): User password for authentication.
    
    Returns:
        tuple[str, requests.Session]: Session ID and requests.Session object if authentication is successful.
    
    Raises:
        SystemExit: If authentication fails or an error occurs.
    """
    login_url: str = f'{lk_url}?action=auth&query=login'
    payload: dict[str, str] = {
        'login': login,
        'psw': password,
        'vl_device_info': json.dumps({
            'appver': '1.40.0',
            'type': 'browser',
            'userAgent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                '(KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'
            )
        })
    }
    headers: dict[str, str] = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'
        )
    }

    logging.info('Trying to establish Mosenergosbyt session')
    session = requests.Session()
    try:
        response = session.post(login_url, data=payload, headers=headers)
        response.raise_for_status()
        result: dict = response.json()
        if result.get('success'):
            session_id: str = result['data'][0]['session']
            logging.info('Successfully authenticated with Mosenergosbyt')
            return session_id, session
        else:
            logging.error('Connection to Mosenergosbyt failed: %s', result.get('error', 'Unknown error'))
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        logging.error('Request to Mosenergosbyt failed: %s', str(e))
        sys.exit(1)
    except (ValueError, KeyError) as e:
        logging.error('Error processing Mosenergosbyt response: %s', str(e))
        sys.exit(1)


def fetch_mosenergo_provider(lk_url: str, session_id: str, session: requests.Session,
                             headers: dict[str, str]) -> str:
    """Fetch provider ID from Mosenergosbyt API.
    
    Args:
        lk_url (str): Base URL of the Mosenergosbyt API.
        session_id (str): Session ID for authentication.
        session (requests.Session): Active session for requests.
        headers (dict[str, str]): Headers for HTTP requests.
    
    Returns:
        str: Provider ID if request is successful.
    
    Raises:
        SystemExit: If request fails or response is invalid.
    """
    session_url: str = f'{lk_url}?action=sql&query=LSList&session={session_id}'
    logging.info('Fetching provider data from Mosenergosbyt')
    try:
        response = session.post(session_url, headers=headers)
        response.raise_for_status()
        result: dict = response.json()
        if result.get('success'):
            provider_id: str = result['data'][0]['vl_provider']
            logging.info('Successfully retrieved provider ID from Mosenergosbyt')
            return provider_id
        else:
            logging.error('Failed to fetch provider data: %s', result.get('error', 'Unknown error'))
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        logging.error('Request to fetch provider data failed: %s', str(e))
        sys.exit(1)
    except (ValueError, KeyError) as e:
        logging.error('Error processing provider data response: %s', str(e))
        sys.exit(1)


def send_mosenergo_data(lk_url: str, session_id: str, session: requests.Session,
                        headers: dict[str, str], provider_id: str, electricity_values: list[float],
                        query_type: str, payload_base: dict) -> dict | None:
    """Send data to Mosenergosbyt API (CalcCharge or SaveIndications).
    
    Args:
        lk_url (str): Base URL of the Mosenergosbyt API.
        session_id (str): Session ID for authentication.
        session (requests.Session): Active session for requests.
        headers (dict[str, str]): Headers for HTTP requests.
        provider_id (str): Provider ID for the request.
        electricity_values (list[float]): List of electricity values to send.
        query_type (str): Type of query ('CalcCharge' or 'SaveIndications').
        payload_base (dict): Base payload dictionary for the request.
    
    Returns:
        dict | None: Response JSON if successful, None if failed.
    
    Raises:
        SystemExit: If request fails.
    """
    if query_type == 'CalcCharge':
        url: str = f'{lk_url}?action=sql&query=bytProxy&session={session_id}'
        payload_base.update({
            'proxyquery': 'CalcCharge',
            'vl_provider': provider_id,
            'vl_t1': electricity_values[0],
            'vl_t2': electricity_values[1]
        })
    else:  # SaveIndications
        url: str = (
            f'{lk_url}?action=sql&query=SaveIndications&'
            f'session={session_id}'
        )
        payload_base.update({
            'vl_provider': provider_id,
            'vl_t1': electricity_values[0],
            'vl_t2': electricity_values[1]
        })

    logging.info('Sending data to Mosenergosbyt (%s)', query_type)
    try:
        response = session.post(url, headers=headers, data=payload_base)
        response.raise_for_status()
        result: dict = response.json()
        logging.info('%s response: %s', query_type, result)
        return result
    except requests.exceptions.RequestException as e:
        logging.error('%s request failed: %s', query_type, str(e))
        if hasattr(e, 'response') and e.response is not None:
            logging.error('Response content: %s', e.response.text)
        return None


def main() -> None:
    """Main function to orchestrate the automation process."""
    # Load environment variables
    env_vars: dict[str, str] = setup_environment()

    setup_logging(log_file_path=env_vars['log_file'])
    current_time: str = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    logging.info('Script started at: %s', current_time)

    # Initialize variables for results and errors
    calc_response: dict | None = None
    save_response: dict | None = None
    success: bool = False
    error_message: str = ""

    try:
        # Authenticate with Saures and fetch meter data
        saures_sid: str = authenticate_saures(
            env_vars['saures_api_url'], env_vars['login'], env_vars['saures_pass']
        )
        meters_data: dict = fetch_saures_meter_data(
            env_vars['saures_api_url'], saures_sid, env_vars['meter_id'], current_time
        )
        
        # Extract electricity values
        electricity_values: list[float] = get_electricity_vals(meters_data)
        if len(electricity_values) < 2:
            logging.error('Not enough electricity values received: %s', electricity_values)
            error_message = 'Not enough electricity values received.'
            raise ValueError(error_message)
        logging.info('Extracted electricity values: %s', electricity_values)

        # Authenticate with Mosenergosbyt and fetch provider data
        session_id, session = authenticate_mosenergo(
            env_vars['mosenergo_lk_url'], env_vars['login'], env_vars['mosenergo_pass']
        )
        headers: dict[str, str] = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                '(KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'
            )
        }
        provider_id: str = fetch_mosenergo_provider(
            env_vars['mosenergo_lk_url'], session_id, session, headers
        )

        # Send data to Mosenergosbyt and collect results for notification
        calc_payload: dict = {
            'nn_phone': '+7 (499) 550-9-550',
            'plugin': 'bytProxy',
            'pr_flat_meter': 0
        }
        save_payload: dict = {
            'plugin': 'propagateMesInd',
            'pr_flat_meter': 0
        }
        calc_response = send_mosenergo_data(
            env_vars['mosenergo_lk_url'], session_id, session, headers, provider_id,
            electricity_values, 'CalcCharge', calc_payload
        )
        save_response = send_mosenergo_data(
            env_vars['mosenergo_lk_url'], session_id, session, headers, provider_id,
            electricity_values, 'SaveIndications', save_payload
        )

        # Check if both operations were successful
        if calc_response and save_response and calc_response.get('success') and save_response.get('success'):
            success = True
            calc_result: str = calc_response['data'][0].get('nm_result', 'No result message available')
            # Remove HTML-tags and bold tags
            calc_result_cleaned = calc_result.replace("<font color='#ff6347'>", "").replace("</font>", "")
            calc_result_cleaned = calc_result_cleaned.replace("<b>", "**").replace("</b>", "**")
            save_result: str = save_response['data'][0].get('nm_result', 'No result message available')
            message: str = (
                '✅ *Mosenergosbyt Operation Success*\n\n'
                f'{calc_result_cleaned}\n'
                f'{save_result}'
            )
        else:
            success = False
            error_message = 'Operation failed. Check logs for details.'
            message: str = (
                '❌ *Mosenergosbyt Operation Failure*\n\n'
                f'Error: {error_message}'
            )

    except Exception as e:
        logging.error('Unexpected error in script execution: %s', str(e))
        success = False
        error_message = str(e)
        message: str = (
            '❌ *Mosenergosbyt Script Unexpected Failure*\n\n'
            f'Error: {error_message}'
        )

    finally:
        # Send Telegram notification regardless of success or failure
        for id_ in env_vars['telegram_chat_id'].split(','):
            send_telegram_message(
                env_vars['telegram_bot_token'], id_, message
            )

        # Clean up
        try:
            session.close()
        except NameError:
            pass
        logging.info('Script completed with status: %s', 'Success' if success else 'Failure')
        
if __name__ == '__main__':
    main()
