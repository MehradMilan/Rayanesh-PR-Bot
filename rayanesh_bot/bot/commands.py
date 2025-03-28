from bot.tasks import join_group_request

JOIN_GROUP_COMMAND = "join_group"
AUTHORIZE_COMMAND = "authorize"
START_COMMAND = "start"
REVEAL_CHAT_ID_COMMAND = "chat_id"
LIST_TASKS_COMMAND = "list_tasks"
CANCEL_COMMAND = "cancel"

DEEPLINK_HANDLERS = {JOIN_GROUP_COMMAND: join_group_request}
