"""Email service using Mailtrap."""

from __future__ import annotations

import logging

import mailtrap as mt

from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_contact_form_email(
    recipient_email: str,
    recipient_name: str,
    subject: str,
    message: str,
) -> bool:
    """
    Send a confirmation email to contact form submitter.

    Args:
        recipient_email: Email of the contact form submitter
        recipient_name: Name of the contact form submitter
        subject: Subject of the contact form
        message: Message content from contact form

    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        client = mt.MailtrapClient(
            token=settings.mailtrap_api_token,
            sandbox=settings.mailtrap_use_sandbox,
            inbox_id=settings.mailtrap_inbox_id,
        )

        # Create confirmation email body
        html_body = f"""
        <!DOCTYPE html>
        <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                    .content {{ margin-bottom: 20px; }}
                    .footer {{ border-top: 1px solid #ddd; padding-top: 20px; font-size: 12px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>Thank You for Contacting Us</h2>
                    </div>
                    <div class="content">
                        <p>Dear {recipient_name},</p>
                        <p>Thank you for reaching out to us. We have received your message and will get back to you as soon as possible.</p>
                        <hr>
                        <h3>Your Message Details:</h3>
                        <p><strong>Subject:</strong> {subject}</p>
                        <p><strong>Message:</strong></p>
                        <p style="background-color: #f9f9f9; padding: 10px; border-left: 4px solid #007bff;">{message}</p>
                        <hr>
                        <p>Our team will review your inquiry and respond to you shortly.</p>
                    </div>
                    <div class="footer">
                        <p>© 2025 Our Company. All rights reserved.</p>
                    </div>
                </div>
            </body>
        </html>
        """

        text_body = f"""
        Thank you for contacting us. We have received your message and will get back to you as soon as possible.

        Subject: {subject}

        Message:
        {message}

        Our team will review your inquiry and respond to you shortly.
        """

        # Create mail object
        mail = mt.Mail(
            sender=mt.Address(
                email=settings.mailtrap_sender_email,
                name=settings.mailtrap_sender_name,
            ),
            to=[mt.Address(email=recipient_email, name=recipient_name)],
            subject=f"Re: {subject}",
            text=text_body,
            html=html_body,
            category="contact-form",
        )

        # Send email
        response = client.send(mail)

        if response and response.get("success"):
            logger.info(f"Contact form confirmation email sent to {recipient_email}")
            return True
        else:
            logger.error(f"Failed to send contact form email to {recipient_email}: {response}")
            return False

    except Exception as e:
        logger.error(f"Exception while sending contact form email: {e}")
        return False


async def send_admin_notification_email(
    admin_email: str,
    submitter_name: str,
    submitter_email: str,
    subject: str,
    message: str,
) -> bool:
    """
    Send a notification email to admin about new contact form submission.

    Args:
        admin_email: Email of the admin to notify
        submitter_name: Name of the contact form submitter
        submitter_email: Email of the contact form submitter
        subject: Subject of the contact form
        message: Message content from contact form

    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        client = mt.MailtrapClient(
            token=settings.mailtrap_api_token,
            sandbox=settings.mailtrap_use_sandbox,
            inbox_id=settings.mailtrap_inbox_id,
        )

        html_body = f"""
        <!DOCTYPE html>
        <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                    .content {{ margin-bottom: 20px; }}
                    .footer {{ border-top: 1px solid #ddd; padding-top: 20px; font-size: 12px; color: #666; }}
                    .alert {{ background-color: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; margin-bottom: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>New Contact Form Submission</h2>
                    </div>
                    <div class="alert">
                        <strong>⚠️ New submission requires attention</strong>
                    </div>
                    <div class="content">
                        <h3>Submission Details:</h3>
                        <p><strong>Submitter Name:</strong> {submitter_name}</p>
                        <p><strong>Submitter Email:</strong> {submitter_email}</p>
                        <p><strong>Subject:</strong> {subject}</p>
                        <hr>
                        <h3>Message:</h3>
                        <p style="background-color: #f9f9f9; padding: 10px; border-left: 4px solid #007bff;">{message}</p>
                        <hr>
                        <p><a href="#">View in admin panel</a> | <a href="mailto:{submitter_email}">Reply to sender</a></p>
                    </div>
                    <div class="footer">
                        <p>© 2025 Our Company. All rights reserved.</p>
                    </div>
                </div>
            </body>
        </html>
        """

        text_body = f"""
        New Contact Form Submission

        Submitter Name: {submitter_name}
        Submitter Email: {submitter_email}
        Subject: {subject}

        Message:
        {message}
        """

        mail = mt.Mail(
            sender=mt.Address(
                email=settings.mailtrap_sender_email,
                name=settings.mailtrap_sender_name,
            ),
            to=[mt.Address(email=admin_email)],
            subject=f"[NEW] Contact Form: {subject}",
            text=text_body,
            html=html_body,
            category="contact-form-admin",
        )

        response = client.send(mail)

        if response and response.get("success"):
            logger.info(f"Admin notification email sent to {admin_email}")
            return True
        else:
            logger.error(f"Failed to send admin notification email: {response}")
            return False

    except Exception as e:
        logger.error(f"Exception while sending admin notification email: {e}")
        return False
