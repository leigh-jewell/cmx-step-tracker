from functools import wraps
from flask_login import current_user
from DBHelper import DBHelper

def admin_login_required(DB):
    def admin_login_required_func(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            print(current_user.get_id())
            if not DB.is_admin(current_user.get_id()):
                print('Not admin.')
                return abort(403)
            print('admin.')
            return func(*args, **kwargs)
        return decorated_view


from flask_admin import BaseView, expose

class HelloView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin-home.html')