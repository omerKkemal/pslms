from flask_login import UserMixin


class SessionUser(UserMixin):
    def __init__(self, user_id, role, username):
        self.id = str(user_id)
        self.role = role
        self.username = username
