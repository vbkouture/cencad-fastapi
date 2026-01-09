"""Email service using Mailtrap."""

from __future__ import annotations

import logging

import mailtrap as mt  # type: ignore[import-untyped]

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


async def send_password_reset_email(
    recipient_email: str,
    recipient_name: str,
    reset_token: str,
) -> bool:
    """
    Send password reset email to user.

    Args:
        recipient_email: Email of the user requesting password reset
        recipient_name: Name of the user
        reset_token: Password reset token

    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        client = mt.MailtrapClient(
            token=settings.mailtrap_api_token,
            sandbox=settings.mailtrap_use_sandbox,
            inbox_id=settings.mailtrap_inbox_id,
        )

        # Construct reset URL from environment configuration
        reset_url = f"{settings.frontend_url}/reset-password?token={reset_token}"

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
                    .button {{ display: inline-block; padding: 12px 24px; background-color: #007bff; color: #ffffff; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                    .footer {{ border-top: 1px solid #ddd; padding-top: 20px; font-size: 12px; color: #666; }}
                    .warning {{ background-color: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>Password Reset Request</h2>
                    </div>
                    <div class="content">
                        <p>Hello {recipient_name},</p>
                        <p>We received a request to reset your password. Click the button below to reset your password:</p>
                        <a href="{reset_url}" class="button">Reset Password</a>
                        <p>Or copy and paste this link into your browser:</p>
                        <p style="background-color: #f9f9f9; padding: 10px; word-break: break-all;">{reset_url}</p>
                        <div class="warning">
                            <strong>⚠️ Security Notice:</strong>
                            <ul>
                                <li>This link will expire in 1 hour</li>
                                <li>If you didn't request this password reset, please ignore this email</li>
                                <li>Your password will not change until you access the link above and create a new one</li>
                            </ul>
                        </div>
                    </div>
                    <div class="footer">
                        <p>© 2025 Our Company. All rights reserved.</p>
                    </div>
                </div>
            </body>
        </html>
        """

        text_body = f"""
        Password Reset Request

        Hello {recipient_name},

        We received a request to reset your password. Copy and paste this link into your browser to reset your password:

        {reset_url}

        This link will expire in 1 hour.

        If you didn't request this password reset, please ignore this email.
        Your password will not change until you access the link above and create a new one.

        Best regards,
        {settings.mailtrap_sender_name}
        """

        mail = mt.Mail(
            sender=mt.Address(
                email=settings.mailtrap_sender_email,
                name=settings.mailtrap_sender_name,
            ),
            to=[mt.Address(email=recipient_email, name=recipient_name)],
            subject="Password Reset Request",
            text=text_body,
            html=html_body,
            category="password-reset",
        )

        response = client.send(mail)

        if response and response.get("success"):
            logger.info(f"Password reset email sent to {recipient_email}")
            return True
        else:
            logger.error(f"Failed to send password reset email to {recipient_email}: {response}")
            return False

    except Exception as e:
        logger.error(f"Exception while sending password reset email: {e}")
        return False


async def send_trainee_invitation_email(
    recipient_email: str,
    recipient_name: str,
    company_name: str,
    temporary_password: str,
) -> bool:
    """
    Send invitation email to new corporate trainee with temporary password.

    Args:
        recipient_email: Email of the trainee being invited
        recipient_name: Name of the trainee
        company_name: Name of the corporate account/company
        temporary_password: Temporary OTP password

    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        client = mt.MailtrapClient(
            token=settings.mailtrap_api_token,
            sandbox=settings.mailtrap_use_sandbox,
            inbox_id=settings.mailtrap_inbox_id,
        )

        login_url = f"{settings.frontend_url}/login"

        html_body = f"""
        <!DOCTYPE html>
        <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 5px; margin-bottom: 20px; color: white; }}
                    .content {{ margin-bottom: 20px; }}
                    .credentials-box {{ background-color: #f8f9fa; border: 2px solid #007bff; border-radius: 5px; padding: 20px; margin: 20px 0; }}
                    .credential-item {{ margin: 10px 0; padding: 10px; background-color: white; border-radius: 3px; }}
                    .credential-label {{ font-weight: bold; color: #666; font-size: 12px; text-transform: uppercase; }}
                    .credential-value {{ font-size: 16px; color: #333; font-family: 'Courier New', monospace; margin-top: 5px; }}
                    .button {{ display: inline-block; padding: 12px 24px; background-color: #007bff; color: #ffffff; text-decoration: none; border-radius: 5px; margin: 20px 0; font-weight: bold; }}
                    .footer {{ border-top: 1px solid #ddd; padding-top: 20px; font-size: 12px; color: #666; }}
                    .warning {{ background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0; border-radius: 3px; }}
                    .steps {{ background-color: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                    .steps ol {{ margin: 10px 0; padding-left: 20px; }}
                    .steps li {{ margin: 8px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1 style="margin: 0; font-size: 24px;">🎓 Welcome to the Learning Platform!</h1>
                    </div>
                    <div class="content">
                        <p>Hello <strong>{recipient_name}</strong>,</p>
                        <p>Great news! <strong>{company_name}</strong> has invited you to join their corporate learning platform. You now have access to professional courses and training materials.</p>

                        <div class="credentials-box">
                            <h3 style="margin-top: 0; color: #007bff;">📧 Your Login Credentials</h3>
                            <div class="credential-item">
                                <div class="credential-label">Email Address</div>
                                <div class="credential-value">{recipient_email}</div>
                            </div>
                            <div class="credential-item">
                                <div class="credential-label">Temporary Password</div>
                                <div class="credential-value" style="color: #dc3545; font-weight: bold;">{temporary_password}</div>
                            </div>
                        </div>

                        <div class="steps">
                            <h3 style="margin-top: 0;">📝 Getting Started</h3>
                            <ol>
                                <li>Click the button below to access the login page</li>
                                <li>Enter your email and temporary password</li>
                                <li>You'll be prompted to create a new secure password</li>
                                <li>Start learning!</li>
                            </ol>
                        </div>

                        <center>
                            <a href="{login_url}" class="button">🚀 Login Now</a>
                        </center>

                        <p style="font-size: 14px; color: #666; margin-top: 20px;">Or copy and paste this link into your browser:</p>
                        <p style="background-color: #f9f9f9; padding: 10px; word-break: break-all; font-size: 12px;">{login_url}</p>

                        <div class="warning">
                            <strong>🔒 Important Security Information:</strong>
                            <ul style="margin: 10px 0;">
                                <li>You <strong>must</strong> change your password on first login</li>
                                <li>Keep your temporary password secure and don't share it</li>
                                <li>Choose a strong password with at least 8 characters</li>
                                <li>If you didn't expect this invitation, please contact your company administrator</li>
                            </ul>
                        </div>

                        <p>If you have any questions or need assistance, please don't hesitate to reach out to your company's learning administrator.</p>

                        <p>Happy learning! 📚</p>
                    </div>
                    <div class="footer">
                        <p><strong>This is an automated message from {company_name}'s learning platform.</strong></p>
                        <p>© 2026 Learning Platform. All rights reserved.</p>
                    </div>
                </div>
            </body>
        </html>
        """

        text_body = f"""
        Welcome to the Learning Platform!

        Hello {recipient_name},

        {company_name} has invited you to join their corporate learning platform.

        YOUR LOGIN CREDENTIALS:
        ========================
        Email: {recipient_email}
        Temporary Password: {temporary_password}

        GETTING STARTED:
        1. Visit: {login_url}
        2. Enter your email and temporary password
        3. Create a new secure password when prompted
        4. Start learning!

        IMPORTANT SECURITY INFORMATION:
        - You MUST change your password on first login
        - Keep your temporary password secure
        - Choose a strong password with at least 8 characters
        - If you didn't expect this invitation, contact your administrator

        If you have any questions, please contact your company's learning administrator.

        Happy learning!

        ---
        This is an automated message from {company_name}'s learning platform.
        © 2026 Learning Platform. All rights reserved.
        """

        mail = mt.Mail(
            sender=mt.Address(
                email=settings.mailtrap_sender_email,
                name=settings.mailtrap_sender_name,
            ),
            to=[mt.Address(email=recipient_email, name=recipient_name)],
            subject=f"🎓 Welcome to {company_name}'s Learning Platform - Your Invitation",
            text=text_body,
            html=html_body,
            category="trainee-invitation",
        )

        response = client.send(mail)

        if response and response.get("success"):
            logger.info(f"Trainee invitation email sent to {recipient_email}")
            return True
        else:
            logger.error(
                f"Failed to send trainee invitation email to {recipient_email}: {response}"
            )
            return False

    except Exception as e:
        logger.error(f"Exception while sending trainee invitation email: {e}")
        return False
