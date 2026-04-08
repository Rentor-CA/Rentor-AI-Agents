"""Build Google Chat card UI responses."""


def welcome_card(agent_name: str) -> dict:
    """Build a welcome card when the bot is added to a space."""
    return {
        "cardsV2": [{
            "cardId": "welcome",
            "card": {
                "header": {
                    "title": f"{agent_name}",
                    "subtitle": "Your personal Rentor AI agent",
                    "imageUrl": "",
                    "imageType": "CIRCLE",
                },
                "sections": [{
                    "widgets": [{
                        "textParagraph": {
                            "text": "I can help you with:\n"
                                    "- Company policies and procedures\n"
                                    "- Daily work tasks and questions\n"
                                    "- Collaborating with other team members' agents\n"
                                    "- Starting video calls for face-to-face chats"
                        }
                    }]
                }],
            },
        }]
    }


def video_call_card(meeting_url: str, agent_name: str) -> dict:
    """Build a card with a video call join button."""
    return {
        "cardsV2": [{
            "cardId": "video_call",
            "card": {
                "header": {
                    "title": "Video Call",
                    "subtitle": f"Chat face-to-face with {agent_name}",
                },
                "sections": [{
                    "widgets": [
                        {
                            "textParagraph": {
                                "text": f"Your agent is joining the meeting."
                            }
                        },
                        {
                            "buttonList": {
                                "buttons": [{
                                    "text": "Join Meeting",
                                    "onClick": {
                                        "openLink": {"url": meeting_url}
                                    },
                                }]
                            }
                        },
                    ]
                }],
            },
        }]
    }


def policy_card(title: str, summary: str) -> dict:
    """Build a card displaying a policy summary."""
    return {
        "cardsV2": [{
            "cardId": "policy",
            "card": {
                "header": {"title": title, "subtitle": "Company Policy"},
                "sections": [{
                    "widgets": [{
                        "textParagraph": {"text": summary}
                    }]
                }],
            },
        }]
    }
