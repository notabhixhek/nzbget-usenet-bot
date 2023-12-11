import logging
import requests
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Set up logging
logging.basicConfig(level=logging.INFO)

# Replace 'YOUR_TELEGRAM_API_TOKEN' with the actual API token from BotFather
TELEGRAM_API_TOKEN = 'YOUR_TELEGRAM_API_TOKEN'
NZBGET_API_URL = 'http://nzbget:tegbzn6789@IP:PORT or URL/jsonrpc'  # Replace with your NZBGet server URL

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Hello! I am your NZBGet bot. Use /status to get the current queue status.')

def format_speed(speed_in_bytes):
    if speed_in_bytes < 1024:
        return f"{speed_in_bytes} B/s"
    elif speed_in_bytes < 1024 ** 2:
        return f"{speed_in_bytes / 1024:.2f} KB/s"
    elif speed_in_bytes < 1024 ** 3:
        return f"{speed_in_bytes / (1024 ** 2):.2f} MB/s"
    else:
        return f"{speed_in_bytes / (1024 ** 3):.2f} GB/s"

def format_size(size_in_bytes):
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB']
    index = 0
    while size_in_bytes >= 1024 and index < len(suffixes)-1:
        size_in_bytes /= 1024.0
        index += 1
    return f"{size_in_bytes:.2f} {suffixes[index]}"

def status(update: Update, context: CallbackContext) -> None:
    try:
        response_status = requests.post(NZBGET_API_URL, json={"method": "status", "id": 1})
        response_status.raise_for_status()
        data_status = response_status.json()

        if "result" in data_status and "ServerPaused" in data_status["result"]:
            status_text = f"NZBGet is {'paused' if data_status['result']['ServerPaused'] else 'running'}.\n"
            status_text += f"Current speed: {format_speed(data_status['result']['DownloadRate'])}\n\n"
        else:
            update.message.reply_text("Failed to fetch NZBGet status.")
            return

        response_groups = requests.post(
            NZBGET_API_URL,
            json={"method": "listgroups", "params": {"NumberOfLogEntries": 0}, "id": 1},
        )
        response_groups.raise_for_status()
        data_groups = response_groups.json()

        if "result" in data_groups:
            groups_info = data_groups["result"]
            if groups_info:
                status_text += "List of currently downloading and queued files:\n"
                for group_info in groups_info:
                    status = group_info['Status']
                    file_info_text = f"- {group_info['NZBName']}\n"
                    file_info_text += f"  Status: {status}\n"
                    
                    if status == 'DOWNLOADING':
                        processed_size = group_info['DownloadedSizeHi'] * (2**32) + group_info['DownloadedSizeLo']
                        actual_size = group_info['FileSizeHi'] * (2**32) + group_info['FileSizeLo']
                        
                        # Calculate percentage completion
                        progress_percentage = (processed_size / actual_size) * 100
                        
                        # Create a progress bar
                        progress_bar = "["
                        progress_bar += "▰" * int(progress_percentage / 10)
                        progress_bar += "▱" * (10 - int(progress_percentage / 10))
                        progress_bar += f"] {progress_percentage:.2f}%"
                        
                        file_info_text += f"  Size: {format_size(processed_size)} processed of {format_size(actual_size)}\n"
                        file_info_text += f"  Progress: {progress_bar}\n"
                    
                    # Add NZB ID information
                    file_info_text += f"  NZB ID: {group_info['NZBID']}\n"
                    
                    status_text += file_info_text

                if status_text == "List of currently downloading and queued files:\n":
                    status_text += "No files are currently downloading or queued."
            else:
                status_text += "No files are currently downloading or queued."
        else:
            status_text += "Failed to fetch NZBGet groups list."

        update.message.reply_text(status_text)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        update.message.reply_text("An error occurred while processing your request. Please try again later.")

def cancel(update: Update, context: CallbackContext) -> None:
    try:
        nzb_id = context.args[0] if context.args else None
        if not nzb_id:
            update.message.reply_text("Please provide an NZB ID to cancel.")
            return

        response_cancel = requests.post(
            NZBGET_API_URL,
            json={"method": "editqueue", "params": ["GroupDelete", 0, "", [int(nzb_id)]], "id": 1}
        )
        response_cancel.raise_for_status()
        data_cancel = response_cancel.json()

        if data_cancel.get("result") is True:
            update.message.reply_text(f"NZB ID {nzb_id} has been removed from the download queue.")
        else:
            update.message.reply_text(f"Failed to remove NZB ID {nzb_id} from the download queue.")


    except Exception as e:
        logging.error(f"An error occurred: {e}")
        update.message.reply_text("An error occurred while processing your request. Please try again later.")

def pause(update: Update, context: CallbackContext) -> None:
    try:
        nzb_id = context.args[0] if context.args else None
        if not nzb_id:
            update.message.reply_text("Please provide an NZB ID to pause.")
            return

        response_pause = requests.post(
            NZBGET_API_URL,
            json={"method": "editqueue", "params": ["GroupPause", 0, "", [int(nzb_id)]], "id": 1}
        )
        response_pause.raise_for_status()
        data_pause = response_pause.json()

        if data_pause.get("result") is True:
            update.message.reply_text(f"Group with NZB ID {nzb_id} has been paused.")
        else:
            update.message.reply_text(f"Failed to pause group with NZB ID {nzb_id}.")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        update.message.reply_text("An error occurred while processing your request. Please try again later.")

def resume(update: Update, context: CallbackContext) -> None:
    try:
        nzb_id = context.args[0] if context.args else None
        if not nzb_id:
            update.message.reply_text("Please provide an NZB ID to resume.")
            return

        response_resume = requests.post(
            NZBGET_API_URL,
            json={"method": "editqueue", "params": ["GroupResume", 0, "", [int(nzb_id)]], "id": 1}
        )
        response_resume.raise_for_status()
        data_resume = response_resume.json()

        if data_resume.get("result") is True:
            update.message.reply_text(f"Group with NZB ID {nzb_id} has been resumed.")
        else:
            update.message.reply_text(f"Failed to resume group with NZB ID {nzb_id}.")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        update.message.reply_text("An error occurred while processing your request. Please try again later.")

# Set up the updater
updater = Updater(token=TELEGRAM_API_TOKEN, use_context=True)
dispatcher = updater.dispatcher

# Register command handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("status", status))
dispatcher.add_handler(CommandHandler("cancel", cancel, pass_args=True))
dispatcher.add_handler(CommandHandler("pause", pause, pass_args=True))
dispatcher.add_handler(CommandHandler("resume", resume, pass_args=True))

# Start the Bot
updater.start_polling()
updater.idle()
