from bot.tasks import join_group_request, share_playlist

JOIN_GROUP_COMMAND = "join_group"
AUTHORIZE_COMMAND = "authorize"
START_COMMAND = "start"
REVEAL_CHAT_ID_COMMAND = "chat_id"
LIST_TASKS_COMMAND = "list_tasks"
CANCEL_COMMAND = "cancel"
ADD_TASK_COMMAND = "add_task"
HELP_COMMAND = "help"
LISTEN_MUSIC_COMMAND = "listen_music"
SEND_MUSIC_COMMAND = "send_music"
CREATE_PLAYLIST_COMMAND = "create_playlist"
MY_PLAYLISTS_COMMAND = "my_playlists"
SHARE_PLAYLIST_COMMAND = "share_playlist"
BATCH_SEND_MUSIC_COMMAND = "batch_send_music"
DONE_BATCH_FORWARD_COMMMAND = "done_batch_forward"

DEEPLINK_HANDLERS = {
    JOIN_GROUP_COMMAND: join_group_request,
    SHARE_PLAYLIST_COMMAND: share_playlist,
}
