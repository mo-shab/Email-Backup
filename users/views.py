import logging
import os
from email import message_from_file
from email.header import decode_header
from email.utils import parsedate_to_datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.views import PasswordResetView
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import (
    CustomUserCreationForm,
    CustomUserLoginForm,
    CustomPasswordResetForm,
    EmailConfigurationForm,
)
from .models import EmailConfiguration
from .utils import (
    test_imap_connection,
    fetch_folders,
    fetch_emails,
    get_stored_emails,
)
import imaplib

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your account has been created successfully!')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

def login_user(request):
    if request.method == 'POST':
        form = CustomUserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                form.add_error(None, 'Invalid username or password')
    else:
        form = CustomUserLoginForm()
    return render(request, 'users/login.html', {'form': form})

def logout_user(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')

@staff_member_required
def admin_user_list(request):
    users = User.objects.all()
    return render(request, 'admin/user_list.html', {'users': users})

def home(request):
    return render(request, 'users/home.html')

@login_required
def dashboard(request):
    return render(request, 'users/dashboard.html')

class CustomPasswordResetView(PasswordResetView):
    form_class = CustomPasswordResetForm
    template_name = 'users/password_reset.html'

@login_required
def email_configuration(request):
    try:
        email_config = EmailConfiguration.objects.get(user=request.user)
        initial_data = {
            'email_address': email_config.email_address,
            'imap_server': email_config.imap_server,
            'smtp_server': email_config.smtp_server,
            'email_password': email_config.email_password,
            'port_imap': email_config.port_imap,
            'port_smtp': email_config.port_smtp,
        }
    except EmailConfiguration.DoesNotExist:
        email_config = None
        initial_data = {}

    form = EmailConfigurationForm(initial=initial_data)

    if request.method == 'POST':
        if 'save_config' in request.POST:
            form = EmailConfigurationForm(request.POST)
            if form.is_valid():
                if email_config:
                    email_config.email_address = form.cleaned_data['email_address']
                    email_config.imap_server = form.cleaned_data['imap_server']
                    email_config.smtp_server = form.cleaned_data['smtp_server']
                    email_config.email_password = form.cleaned_data['email_password']
                    email_config.port_imap = form.cleaned_data['port_imap']
                    email_config.port_smtp = form.cleaned_data['port_smtp']
                else:
                    email_config = EmailConfiguration(
                        user=request.user,
                        email_address=form.cleaned_data['email_address'],
                        imap_server=form.cleaned_data['imap_server'],
                        smtp_server=form.cleaned_data['smtp_server'],
                        email_password=form.cleaned_data['email_password'],
                        port_imap=form.cleaned_data['port_imap'],
                        port_smtp=form.cleaned_data['port_smtp'],
                    )
                email_config.save()
                messages.success(request, "Configuration saved successfully.")
                logger.info("Email configuration saved successfully for user %s.", request.user)
                return redirect('email_configuration')

        elif 'test_config' in request.POST:
            logger.info("Test button clicked. Starting Email Configuration tests...")
            if email_config:
                imap_status, imap_message = test_imap_connection(
                    email_config.imap_server,
                    email_config.port_imap,
                    email_config.email_address,
                    email_config.email_password
                )
                if imap_status:
                    messages.success(request, "Email Configuration tests passed!")
                else:
                    messages.error(request, f"Email Configuration Test Failed: {imap_message}")
            else:
                messages.error(request, "No configuration found. Please save the configuration first.")

    return render(request, 'users/email_configuration.html', {'form': form, 'email_config': email_config})

@login_required
def fetch_folders_view(request):
    if request.method == "POST":
        email_config = EmailConfiguration.objects.filter(user=request.user).first()
        if email_config:
            try:
                result = fetch_folders(
                    imap_server=email_config.imap_server,
                    port=email_config.port_imap,
                    email_address=email_config.email_address,
                    email_password=email_config.email_password,
                    username=request.user.username,
                )
                if result:
                    messages.success(request, "Folders synchronized successfully!")
                else:
                    messages.info(request, "No new folders detected.")
            except Exception as e:
                messages.error(request, f"Error during folder synchronization: {e}")
        else:
            messages.error(request, "No email configuration found. Please configure your email first.")
        return redirect('email_configuration')
    return redirect('email_configuration')

@login_required
def fetch_emails_view(request):
    email_config = EmailConfiguration.objects.filter(user=request.user).first()
    if not email_config:
        messages.error(request, "No email configuration found. Please configure your email first.")
        return redirect("email_configuration")

    # Fetch available folders dynamically
    base_storage_path = os.path.join("users", "media", f"Email-{request.user.username}", email_config.email_address)
    folders = []
    if os.path.exists(base_storage_path):
        raw_folders = [name for name in os.listdir(base_storage_path) if os.path.isdir(os.path.join(base_storage_path, name))]
        # Extract only the last part of the folder name
        folders = [{"raw": name, "display": name.split(".")[-1]} for name in raw_folders]

    emails = []

    if request.method == "POST":
        folder = request.POST.get("folder", "INBOX")
        try:
            # Attempt to fetch emails using the IMAP connection
            success, result = fetch_emails(
                imap_server=email_config.imap_server,
                port=email_config.port_imap,
                email_address=email_config.email_address,
                email_password=email_config.email_password,
                username=request.user.username,
                folder=folder
            )

            if success:
                emails = result  # Assuming 'result' contains a list of emails
                messages.success(request, f"Successfully fetched emails from the {folder} folder.")
            else:
                # Display a more user-friendly error message based on the result
                if "BAD" in result:  # Checking for a common IMAP error type
                    messages.error(request, f"There was an issue accessing the {folder} folder. Please try again.")
                elif "NO" in result:
                    messages.error(request, f"The {folder} folder does not contain any emails to fetch.")
                else:
                    messages.error(request, f"An unexpected error occurred: {result}")

        except Exception as e:
            messages.error(request, f"Error during email synchronization: {str(e)}")

        return render(request, 'users/fetch_emails.html', {'folders': folders, 'emails': emails})

    return render(request, "users/fetch_emails.html", {"folders": folders, "emails": emails})

@login_required
def get_stored_emails(username, email_address, folder):
    base_dir = os.path.join("users", "media", f"Email-{username}", email_address, folder)
    if not os.path.exists(base_dir):
        return []

    email_files = [f for f in os.listdir(base_dir) if f.endswith(".eml")]
    stored_emails = []

    for email_file in email_files:
        email_path = os.path.join(base_dir, email_file)
        with open(email_path, 'r') as f:
            msg = message_from_file(f)

        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding if encoding else 'utf-8')
        sender = msg.get("From")
        date = parsedate_to_datetime(msg.get("Date")).strftime("%Y-%m-%d %H:%M:%S") if msg.get("Date") else None
        
        attachments = []
        for part in msg.walk():
            content_disposition = str(part.get("Content-Disposition"))
            if "attachment" in content_disposition:
                filename = part.get_filename()
                content_type = part.get_content_type()
                attachments.append({'filename': filename, 'content_type': content_type})

        email_info = {'subject': subject, 'sender': sender, 'date': date, 'attachments': attachments}
        stored_emails.append(email_info)

    return stored_emails

@login_required
def folder_emails_view(request):
    folder = request.GET.get("folder", "INBOX")  # Default to 'INBOX'

    # Retrieve the email configuration for the logged-in user
    email_config = EmailConfiguration.objects.filter(user=request.user).first()
    if not email_config:
        messages.error(request, "No email configuration found. Please configure your email first.")
        return redirect('email_configuration')

    email_address = email_config.email_address  # Get the configured email address
    base_storage_path = os.path.join("users", "media", f"Email-{request.user.username}", email_address)

    # Ensure the user's email storage directory exists
    if not os.path.exists(base_storage_path):
        messages.error(request, "No email backup found on the server.")
        return redirect('email_configuration')

    # Get the list of available folders
    folders = [name for name in os.listdir(base_storage_path) if os.path.isdir(os.path.join(base_storage_path, name))]

    if not folders:
        messages.error(request, "No folders found in your email backup.")
        return redirect('email_configuration')

    # Validate the folder parameter
    if folder not in folders:
        messages.warning(request, f"Invalid folder selected. Defaulting to 'INBOX'.")
        folder = "INBOX"

    # Retrieve stored emails for the selected folder
    emails = get_stored_emails(request.user.username, email_address, folder)

    return render(request, "users/folder_emails.html", {
        "emails": emails,
        "folder": folder,
        "folders": folders,  # Pass the folder list to the template
    })

@login_required
def email_detail_view(request, folder, email_id):
    try:
        print("Call from view")

        # Retrieve the user's email configuration
        email_config = EmailConfiguration.objects.filter(user=request.user).first()
        if not email_config:
            messages.error(request, "No email configuration found. Please configure your email first.")
            return redirect('email_configuration')

        # Get stored emails for the user's specific folder
        stored_emails = get_stored_emails(request.user.username, email_config.email_address, folder)

        # Find the specific email by ID
        email = next((e for e in stored_emails if e['id'] == email_id), None)
        if not email:
            messages.error(request, "Email not found.")
            return redirect('folder_emails_view')

        # Debugging attachment structure
        print("Attachments:", email.get("attachments", []))

        # Update email to include full paths for attachments
        email['attachments'] = [
            {
                "filename": attachment.get("filename", "Unknown File"),
                "filepath": f"{attachment.get('filepath', '')}" if attachment.get("filepath") else None,
            }
            for attachment in email.get("attachments", [])
        ]
        print(f"Email: {email}")

        return render(request, "users/email_detail.html", {"email": email})

    except imaplib.IMAP4_SSL.error as e:
        # Handle IMAP errors such as connection or FETCH errors
        messages.error(request, f"An error occurred while fetching your email. Please try again later. ({str(e)})")
        return redirect('folder_emails_view')

    except Exception as e:
        # Handle any other general errors
        messages.error(request, "Something went wrong. Please try again later.")
        print(f"Unexpected error: {str(e)}")
        return redirect('folder_emails_view')
