"""Test the trainee invitation email."""

import asyncio

from app.core.email_service import send_trainee_invitation_email


async def test_email():
    """Test sending a trainee invitation email."""
    print("Sending test trainee invitation email...\n")

    success = await send_trainee_invitation_email(
        recipient_email="test.trainee@example.com",
        recipient_name="John Doe",
        company_name="Acme Corporation",
        temporary_password="aB7!xY2@pQ",
    )

    if success:
        print("✅ Email sent successfully!")
        print("\nCheck your Mailtrap inbox to see the email.")
        print("\nEmail details:")
        print("  To: test.trainee@example.com")
        print("  Subject: 🎓 Welcome to Acme Corporation's Learning Platform - Your Invitation")
        print("  Contains: Login credentials and getting started instructions")
    else:
        print("❌ Failed to send email")
        print("\nPlease check:")
        print("  1. MAILTRAP_API_TOKEN is set in your .env file")
        print("  2. MAILTRAP_USE_SANDBOX=True for testing")
        print("  3. Your Mailtrap account is active")


if __name__ == "__main__":
    asyncio.run(test_email())
