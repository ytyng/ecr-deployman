import os

import requests


def send_slack_message(
    *,
    webhook_url: str,
    channel: str = '#test',
    text: str = '',
    blocks: list | None = None,
    attachments: list | None = None,
    icon_emoji: str = ':package:',
    username: str = 'ecr-deployman',
    **kwargs,
) -> requests.Response:
    """Send a message to a channel."""

    payload = {
        'channel': channel,
        'username': username,
        'icon_emoji': icon_emoji,
    }
    if text:
        payload['text'] = text
    if blocks:
        payload['blocks'] = blocks
    if attachments:
        payload['attachments'] = attachments

    return requests.post(webhook_url, json=payload)
