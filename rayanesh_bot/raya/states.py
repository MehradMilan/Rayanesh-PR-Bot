SELECT_GROUP, ENTER_DOC_LINK, CONFIRM_DOC, ACCESS_LEVEL = range(
    4
)  # Give document access to group steps
SELECT_GROUP, ENTER_DOC_LINK = range(2)  # Revoke document access from group
SELECT_GROUP, SELECT_USER = range(2)  # Remove user from a group
SELECT_GROUP, RECEIVE_NOTIFICATION_MESSAGE, RECEIVE_SCHEDULE_TIME, CONFIRM_SCHEDULE = (
    range(1000, 1004)
)  # Send notification to users via Rayanesh telegram bot
