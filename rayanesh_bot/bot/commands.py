from bot.tasks import join_group_request

JOIN_GROUP_COMMAND = "join_group"
AUTHORIZE_COMMAND = "authorize"
START_COMMAND = "start"
CANCEL_COMMAND = "cancel"

DEEPLINK_HANDLERS = {JOIN_GROUP_COMMAND: join_group_request}
