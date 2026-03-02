"""
tools/email_notifier.py
Sends email notifications via Gmail SMTP when new leads arrive.
Requires GMAIL_ADDRESS and GMAIL_APP_PASSWORD in .env.
"""

import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

GMAIL_ADDRESS      = os.getenv('GMAIL_ADDRESS')
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')
NOTIFY_EMAIL       = os.getenv('NOTIFY_EMAIL', GMAIL_ADDRESS)
SMTP_HOST          = 'smtp.gmail.com'
SMTP_PORT          = 587

logger = logging.getLogger(__name__)


def _send(subject: str, body_html: str, body_text: str) -> dict:
    """
    Internal helper. Sends from GMAIL_ADDRESS to NOTIFY_EMAIL.
    Returns {'success': True} or {'success': False, 'error': str}
    """
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        logger.warning('Email notification skipped: GMAIL credentials not set in .env')
        return {'success': False, 'error': 'GMAIL credentials not configured'}

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From']    = f'Keystone Growth Partners <{GMAIL_ADDRESS}>'
    msg['To']      = NOTIFY_EMAIL

    msg.attach(MIMEText(body_text, 'plain'))
    msg.attach(MIMEText(body_html, 'html'))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, NOTIFY_EMAIL, msg.as_string())
        return {'success': True}
    except smtplib.SMTPAuthenticationError:
        logger.error('SMTP auth failed — check GMAIL_APP_PASSWORD in .env')
        return {'success': False, 'error': 'SMTP authentication failed'}
    except Exception as e:
        logger.error(f'Email send failed: {e}')
        return {'success': False, 'error': str(e)}


def notify_new_subscriber(email: str, ip_address: str = None) -> dict:
    """Send notification when someone submits the CTA email capture form."""
    subject   = f'New Subscriber: {email}'
    body_text = (
        f'New email subscriber on Keystone Growth Partners website.\n\n'
        f'Email: {email}\n'
        f'IP: {ip_address or "Unknown"}\n'
        f'Source: CTA Form\n'
    )
    body_html = f"""
<html><body style="font-family:sans-serif;color:#222;padding:24px;max-width:540px;">
  <h2 style="color:#B8912E;margin-bottom:4px;">New Subscriber</h2>
  <p style="color:#888;font-size:13px;margin-top:0;">Keystone Growth Partners Website</p>
  <hr style="border:none;border-top:1px solid #eee;margin:16px 0;">
  <p><strong>Email:</strong> {email}</p>
  <p><strong>Source:</strong> CTA Form</p>
  <p><strong>IP Address:</strong> {ip_address or 'Unknown'}</p>
</body></html>
"""
    return _send(subject, body_html, body_text)


def notify_new_contact(name: str, email: str, message: str, ip_address: str = None) -> dict:
    """Send notification when someone submits the contact modal form."""
    subject   = f'New Contact: {name} <{email}>'
    body_text = (
        f'New contact form submission on Keystone Growth Partners website.\n\n'
        f'Name: {name}\n'
        f'Email: {email}\n'
        f'IP: {ip_address or "Unknown"}\n\n'
        f'Message:\n{message}\n'
    )
    body_html = f"""
<html><body style="font-family:sans-serif;color:#222;padding:24px;max-width:540px;">
  <h2 style="color:#B8912E;margin-bottom:4px;">New Contact Form Submission</h2>
  <p style="color:#888;font-size:13px;margin-top:0;">Keystone Growth Partners Website</p>
  <hr style="border:none;border-top:1px solid #eee;margin:16px 0;">
  <p><strong>Name:</strong> {name}</p>
  <p><strong>Email:</strong> <a href="mailto:{email}">{email}</a></p>
  <p><strong>IP Address:</strong> {ip_address or 'Unknown'}</p>
  <p><strong>Message:</strong></p>
  <blockquote style="border-left:3px solid #D4A843;margin:0;padding:12px 16px;background:#fafafa;color:#333;">
    {message.replace(chr(10), '<br>')}
  </blockquote>
</body></html>
"""
    return _send(subject, body_html, body_text)
