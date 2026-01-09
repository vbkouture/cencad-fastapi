"""Value objects for contact forms."""

from enum import StrEnum, auto


class ContactFormStatus(StrEnum):
    """Status of a contact form submission."""

    PENDING = auto()
    READ = auto()
    IN_PROGRESS = auto()
    REPLIED = auto()
    DISCARDED = auto()
