from django.conf import settings
import imaplib

def test_imap_connection(imap_server, port, email_address, email_password):
    try:
        # Connect to the IMAP server
        mail = imaplib.IMAP4_SSL(imap_server, port)
        # Log in using the provided credentials
        mail.login(email_address, email_password)
        mail.logout()
        return True, "IMAP connection successful."
    except Exception as e:
        return False, f"IMAP connection failed: {e}"


import imaplib
import os
def fetch_folders(imap_server, port, email_address, email_password, username):
    try:
        # Connect to the IMAP server
        imap = imaplib.IMAP4_SSL(imap_server, port)
        imap.login(email_address, email_password)

        # Fetch folder names
        status, folders = imap.list()
        if status != "OK":
            return False, "Unable to fetch folders."

        # Define the base directory for user-specific email folders
        base_dir = os.path.join("users", "media", f"Email-{username}", email_address)
        print(f"Base directory: {base_dir}")

        # Create the base directory if it doesn't exist
        os.makedirs(base_dir, exist_ok=True)

        # Keep track of new folders
        new_folders = []

        # Loop through the folders and create them if they don't exist
        for folder in folders:
            print(f"Folder: {folder}")

            # Extract the folder name (last part of the IMAP list entry)
            folder_details = folder.decode().split(' ')
            folder_name = folder_details[-1].strip('"')  # Extract and clean the folder name
            print(f"Extracted Folder Name: {folder_name}")

            folder_path = os.path.join(base_dir, folder_name)  # Path for folder

            # Check if the folder exists locally, if not create it
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
                new_folders.append(folder_name)

        # Close the IMAP connection
        imap.logout()

        # Check for new folders and return the corresponding message
        if new_folders:
            return True, f"New folders created: {', '.join(new_folders)}"
        else:
            return True, "No new folders detected."

    except Exception as e:
        # Handle exceptions and return the error message
        return False, str(e)


import imaplib
import email
from email.header import decode_header
import os
import time


def fetch_emails(imap_server, port, email_address, email_password, username, folder):
    try:
        # Connect to the IMAP server
        imap = imaplib.IMAP4_SSL(imap_server, port)
        imap.login(email_address, email_password)

        # Select the folder
        status, messages = imap.select(folder)
        if status != "OK":
            return False, f"Unable to select folder: {folder}. Check folder name or permissions."

        # Directory for storing emails
        base_dir = os.path.join("users", "media", f"Email-{username}", email_address, folder)
        os.makedirs(base_dir, exist_ok=True)

        fetched_emails = []
        for num in messages[0].split():
            status, data = imap.fetch(num, "(RFC822)")
            if status != "OK":
                continue

            # Parse the email
            msg = email.message_from_bytes(data[0][1])
            subject, encoding = decode_header(msg["Subject"])[0]
            subject = subject.decode(encoding or 'utf-8') if isinstance(subject, bytes) else subject
            sender = msg.get("From")
            date = msg.get("Date")

            # Save email as .eml
            eml_filename = f"{num.decode()}.eml"
            eml_path = os.path.join(base_dir, eml_filename)
            with open(eml_path, "wb") as eml_file:
                eml_file.write(data[0][1])

            # Save attachments
            attachments = []
            for part in msg.walk():
                if part.get_content_disposition() == "attachment":
                    filename = part.get_filename() or f"attachment-{int(time.time())}.bin"
                    filename = filename.replace("/", "_").replace("\\", "_")
                    file_path = os.path.join(base_dir, filename)
                    with open(file_path, "wb") as f:
                        f.write(part.get_payload(decode=True))
                    attachments.append({
                        "filename": filename,
                        "filepath": os.path.join("users/media", f"Email-{username}", email_address, folder, filename),
                    })

            # Append to fetched emails
            fetched_emails.append({
                "subject": subject,
                "sender": sender,
                "date": date,
                "attachments": attachments,
            })

        # Logout and return the emails
        imap.logout()
        return True, fetched_emails
    except Exception as e:
        return False, f"Error: {str(e)}"


def get_last_fetched_id(folder):
    # Implement logic to get the last fetched email ID (e.g., from a file or database)
    try:
        with open(f"{folder}_last_fetched_id.txt", "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        return None  # No last fetched ID, so we fetch all emails

def update_last_fetched_id(folder, last_fetched_id):
    # Implement logic to save the last fetched email ID
    with open(f"{folder}_last_fetched_id.txt", "w") as file:
        file.write(last_fetched_id)

from email import message_from_file
from email.utils import parsedate_to_datetime


def get_stored_emails(username, email_address, folder):
    base_dir = os.path.join("users", "media", f"Email-{username}", email_address, folder)
    if not os.path.exists(base_dir):
        return []

    email_files = [f for f in os.listdir(base_dir) if f.endswith(".eml")]
    stored_emails = []

    for idx, email_file in enumerate(email_files):
        email_path = os.path.join(base_dir, email_file)
        with open(email_path, 'r') as f:
            msg = message_from_file(f)

        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding if encoding else 'utf-8')

        sender = msg.get("From")
        date = parsedate_to_datetime(msg.get("Date")).strftime("%Y-%m-%d %H:%M:%S") if msg.get("Date") else None

        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
        else:
            body = msg.get_payload(decode=True).decode()

        attachments = []
        for part in msg.walk():
            content_disposition = str(part.get("Content-Disposition"))
            if "attachment" in content_disposition:
                attachments.append({
                    "filename": part.get_filename(),
                    "filepath": f"{settings.MEDIA_URL}Email-{username}/{email_address}/{folder}/{part.get_filename()}",
                })

        stored_emails.append({
            "id": idx,
            "subject": subject,
            "sender": sender,
            "date": date,
            "body": body,
            "attachments": attachments,
            "folder": folder,
        })

    return stored_emails