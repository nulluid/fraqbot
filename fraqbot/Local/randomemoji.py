import logging
import os
import random
import sys

from Legobot.Connectors.Slack import Slack
from Legobot.Lego import Lego


logger = logging.getLogger(__name__)
LOCAL_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)))

if LOCAL_DIR not in sys.path:
    sys.path.append(LOCAL_DIR)


from helpers import utils  # noqa: E402


class RandomEmoji(Lego):
    def __init__(self, baseplate, lock, *args, **kwargs):
        super().__init__(baseplate, lock, acl=kwargs.get('acl'))
        self._set_client()
        self.max_how_many = 20
        self.min_how_many = 1
        self.default_how_many = 5

    def listening_for(self, message):
        text = str(message.get('text', ''))
        msg_type = utils.jsearch('metadata.subtype', message)

        return msg_type is None and text.startswith('!emoji')

    def _set_client(self):
        self.client = None
        children = self.baseplate._actor.children

        if children:
            slack = [a._actor for a in children if isinstance(a._actor, Slack)]
            if slack:
                self.client = slack[0].botThread.slack_client

    def _fetch_slack_emojis(self):
        return utils.call_slack_api(
                self.client,
                'emoji.list',
                False,
                'emoji'
            )

    def _get_emoji(self, how_many):
        how_many_limited = max(
            self.min_how_many,
            min(self.max_how_many, how_many)
        )

        emoji_response = self._fetch_slack_emojis()

        return (':'
                + ': :'.join(random.choices(
                        list(emoji_response.keys()), k=how_many_limited
                    )).strip()
                + ':')

    def handle(self, message):
        logger.debug(
            'Handling Random Emoji request: {}'.format(message['text'])
        )
        text_provided = message['text'][6:].strip()

        opts = self.build_reply_opts(message)
        if len(text_provided) > 0 and not text_provided.isdigit():
            return self.reply(
                message,
                '\'{}\' is not a valid integer.'.format(text_provided),
                opts
            )

        how_many = int(text_provided or self.default_how_many)

        random_emojis = self._get_emoji(how_many)
        self.reply(message, random_emojis, opts)

    def get_name(self):
        return 'Random_Emoji'

    def get_help(self):
        return ('Get a random Emoji (or multiple!).'
                + 'Usage: !emoji <how_many[default=5]>')
