from pydantic import BaseModel, Field


class TelegramUser(BaseModel):
    addedToAttachmentMenu: bool = Field(
        None, description="True, if this user added the bot to the attachment menu."
    )
    allowsWriteToPm: bool = Field(
        None, description="True, if this user allowed the bot to message them."
    )
    firstName: str = Field(..., description="First name of the user or bot.")
    id: int = Field(..., description="A unique identifier for the user or bot.")
    isBot: bool = Field(
        None,
        description="True, if this user is a bot. Returned in the `receiver` field only.",
    )
    isPremium: bool = Field(
        None, description="True, if this user is a Telegram Premium user."
    )
    lastName: str = Field(None, description="Last name of the user or bot.")
    languageCode: str = Field(
        None,
        description="IETF language tag of the user's language. Returns in user field only.",
    )
    photoUrl: str = Field(
        None,
        description="URL of the user’s profile photo. The photo can be in .jpeg or .svg formats. Only returned for Mini Apps launched from the attachment menu.",
    )
    username: str = Field(None, description="Username of the user or bot.")
