# Author: Leigh Jewell (ljewell)
from flask import Flask
from flask import redirect
from flask import render_template
from flask import request, Response
from flask import url_for
from flask_login import LoginManager
from flask_login import login_required
from flask_login import login_user
from flask_login import logout_user
from flask_login import current_user
from flask import abort
from flask_bootstrap import Bootstrap
from flask_api import status
from flask import Response
import logging
from logging import Formatter
import json
from DBHelper import DBHelper
from CMXHelper import CMXHelper
from SparkHelper import SparkHelper
from point import Point
import passwordhelper
from user import User
from forms import RegistrationForm
from forms import LeaderboardForm
from forms import AddDevice
from forms import SparkLeaderboardForm
from functools import wraps
import datetime
from measurement.measures import Distance
from time import strftime

def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('config.ini')
    if not 'MAX_MOVING_ANGLE' in app.config:
        app.config['MAX_MOVING_ANGLE'] = 90
    if not 'MAX_TRANSACTIONS' in app.config:
            app.config['MAX_TRANSACTIONS'] = 180
    if not 'MAX_MTRS_SEC' in app.config:
        app.config['MAX_MTRS_SEC'] = 4.42
    app.secret_key = app.config['APP_SECRET_KEY']
    logging_level = app.config['LOG_LEVEL']
    filename = app.config['LOGFILE'] + "-" + strftime("%Y%m%d%H%M") + ".log"
    handler = logging.FileHandler(filename)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'
    ))
    if "DEBUG" in logging_level:
        app.logger.setLevel(logging.DEBUG)
    elif "INFO" in logging_level:
        app.logger.setLevel(logging.INFO)
    app.logger.addHandler(handler)

    return app


app = create_app()
login_manager = LoginManager(app)
bootstrap = Bootstrap(app)
DB = DBHelper(app)
PH = passwordhelper.PasswordHelper()
CMX = CMXHelper(app)
SPARK = SparkHelper(app)


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid. Just used for CMX notification authentication.
    HTTP HEADER
    """
    if app.config['NOTIFICATION_USER']:
        notification_user = app.config['NOTIFICATION_USER']
    else:
        app.logger.info("check_auth(): config.ini missing NOTIFICATION_USER")
        notification_user = None
    if app.config['NOTIFICATION_PASSWORD']:
        notification_password = app.config['NOTIFICATION_PASSWORD']
    else:
        app.logger.info("check_auth(): config.ini missing NOTIFICATION_PASSWORD")
        notification_password = None

    return username == notification_user and password == notification_password

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with valid credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@login_manager.user_loader
def load_user(user_id):
    user_password = DB.get_user(user_id)
    if user_password:
        return User(user_id)


def admin_login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not DB.is_admin(current_user.get_id()):
            return abort(403)
        return func(*args, **kwargs)
    return decorated_view


def myconverter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()

@app.route("/adm", methods=['GET','POST'])
@login_required
@admin_login_required
def admin_home():
    report_records = request.form.get("report_records")
    if report_records is None:
        report_records = 100
    total_devices = DB.total_devices()
    total_users = DB.total_users()
    total_tracked = DB.total_tracked_devices()
    count_history = DB.total_counts(report_records)
    if len(count_history) > 0:
        seq = [row['notification_count'] for row in count_history]
        max_peak_notification = round(max(seq)/60,1)
        max_peak_percent = round((max_peak_notification/app.config['MAX_TRANSACTIONS'])*100,1)
    else:
        max_peak_notification = 0
        max_peak_percent = 0
    count_history_json = json.dumps(count_history, default=myconverter)

    return render_template('admin-home.html', total_devices = total_devices, total_users = total_users,
                           total_tracked = total_tracked, max_peak_notification = max_peak_notification,
                           max_peak_percent = max_peak_percent, count_history_json = count_history_json,
                           max_transactions = app.config['MAX_TRANSACTIONS'], report_records=report_records)


@app.route("/admin-leaderboard-date", methods=['GET','POST'])
@login_required
@admin_login_required
def admin_leaderboard_date():
    form = LeaderboardForm(request.form)
    if request.method == 'POST' and form.validate():
        date = form.date.data
        number_delegates = form.number_delegates.data
        format = form.format.data
    if request.method == 'GET':
        number_delegates = 50
        date = datetime.datetime.now().strftime('%Y-%m-%d')
        format = "graph"
    top_devices_date = DB.get_num_devices_date(number_delegates, date, exclude=False)
    top_devices_json = json.dumps(top_devices_date, default=myconverter)
    app.logger.debug('admin_leaderboard_date(): got {} number of devices to display'.format(len(top_devices_date)))

    return render_template('admin-leaderboard-date.html', leaderboardform=form, devices_date=top_devices_date,
                           date=date, number_delegates=number_delegates, top_devices_json=top_devices_json,
                           format=format)


@app.route("/admin-leaderboard", methods=['GET','POST'])
@login_required
@admin_login_required
def admin_leaderboard():
    if request.method == 'POST':
        format = request.form.get("format")
    else:
        format = "graph"
    top_devices = DB.get_num_devices(50, exclude=False)
    top_devices_json = json.dumps(top_devices, default=myconverter)
    app.logger.debug('admin_leaderboard(): got {} number of devices to display'.format(len(top_devices)))

    return render_template('admin-leaderboard.html', devices=top_devices,
                           top_devices_json=top_devices_json, format=format)

@app.route("/admin-leaderboard-spark", methods=['GET','POST'])
@login_required
@admin_login_required
def admin_leaderboard_spark():
    form = LeaderboardForm(request.form)
    if request.method == 'POST' and form.validate():
        date = form.date.data
        number_delegates = form.number_delegates.data
    if request.method == 'GET':
        number_delegates = 10
        date = datetime.datetime.now().strftime('%Y-%m-%d')
    top_devices_date = DB.get_num_devices_date(number_delegates, date)
    app.logger.debug('admin_leaderboard_spark(): got {} number of devices to display'.format(len(top_devices_date)))

    return render_template('admin-leaderboard-spark.html', leaderboardform=form,
                           date=date, number_delegates=number_delegates, devices_date=top_devices_date)


@app.route("/admin-leaderboard-spark-message", methods=['POST'])
@login_required
@admin_login_required
def admin_leaderboard_spark_message():
    message = request.form.get("spark_post")
    SPARK.post_room(message)
    app.logger.debug('admin_leaderboard_spark_message(): posted message {}'.format(message))

    return redirect(url_for('admin_leaderboard_spark'))


@app.route("/admin-leaderboard-cisco", methods=['GET','POST'])
@login_required
@admin_login_required
def admin_leaderboard_cisco():
    if request.method == 'POST':
        format = request.form.get("format")
    else:
        format = "graph"
    top_devices = DB.get_num_devices(50, '%@cisco.com', False)
    top_devices_json = json.dumps(top_devices, default=myconverter)
    app.logger.debug('admin_leaderboard_cisco(): got {} number of devices to display'.format(len(top_devices)))

    return render_template('admin-leaderboard-cisco.html', devices=top_devices,
                           top_devices_json=top_devices_json, format=format)


@app.route("/admin-accounts", methods=['GET','POST'])
@login_required
@admin_login_required
def admin_account():
    users = {}
    if request.method == 'POST':
        search_str = request.form.get("search")
        users = DB.get_all_users(search_str)

    return render_template('admin-account.html', users=users)


@app.route("/admin-devices", methods=['GET','POST'])
@login_required
@admin_login_required
def admin_device():
    devices = {}
    if request.method == 'POST':
        search_str = request.form.get("search")
        devices = DB.get_all_devices(search_str)

    return render_template('admin-devices.html', devices=devices)


@app.route("/account/update_user", methods=['POST'])
@login_required
@admin_login_required
def account_update_user():
    if 'admin@cisco.com' == current_user.get_id():
        if request.form['submit'] == 'delete':
            email = request.form.get("email")
            app.logger.info("account_update_user(): email {} delete requested.".format(email))
            DB.delete_user(email)
            SPARK.delete_user(email)
        elif request.form['submit'] == 'update':
            email = request.form.get("email")
            nickname = request.form.get("nickname")
            new_nickname = request.form.get("new_nickname")
            password = request.form.get("password")
            confirm_password = request.form.get("confirm_password")
            if request.form.get('is_admin') == "True":
                is_admin = True
                if not request.form.get('new_is_admin'):
                     new_is_admin = False
                else:
                    new_is_admin = True
            elif request.form.get('is_admin') == "False":
                is_admin = False
                if request.form.get('new_is_admin'):
                    new_is_admin = True
                else:
                    new_is_admin = False
            app.logger.info("account_update_user(): update account email {} name {} is_admin {}".format(email, nickname, is_admin))
            if len(password)> 0:
                if password == confirm_password:
                    salt = PH.get_salt()
                    hashed = PH.get_hash(password + salt)
                    DB.reset_user_password(email, salt, hashed)
                else:
                    app.logger.error("account_update_user(): Reset password failed for {}, passwords not equal".format(email))
            if new_nickname != nickname:
                if len(new_nickname) > 0:
                    app.logger.debug("account_update_user(): Reset username requested for {} new {} old {}".format(email, new_nickname, nickname))
                    DB.update_user_name(email, new_nickname)
                else:
                    app.logger.error("account_update_user(): Reset name failed for {} current {} new {}".format(email, nickname, new_nickname))
            print("DEBUG DEBUG", request.form.get("new_is_admin"), request.form.get("is_admin"))
            if is_admin != new_is_admin:
                app.logger.debug(
                    "account_update_user(): email {} change admin status requested from {} to {}".format(email, is_admin, new_is_admin))
                if DB.make_user_admin(email, new_is_admin) <= 0:
                    app.logger.error(
                        "account_update_user(): email {} unable to change admin status to {}".format(email,
                                                                                                     new_is_admin))
        elif request.form['submit'] == 'add':
            email = request.form.get("email")
            nickname = request.form.get("nickname")
            password = request.form.get("password")
            is_admin = False
            confirm_password = request.form.get("confirm_password")
            if len(password) > 5 and password == confirm_password:
                salt = PH.get_salt()
                hashed = PH.get_hash(password + salt)
                if "@" in email and len(email) > 5:
                    if DB.add_user(email, salt, hashed, is_admin, nickname) <= 0:
                        app.logger.error(
                            "account_update_user(): Add user to db failed {}".format(
                                email))
                else:
                    app.logger.error(
                        "account_update_user(): Add user failed {}, email not great than 5 chars".format(
                            email))
            else:
                app.logger.error("account_update_user(): Add user failed {}, passwords not equal or not great than 5 chars".format(email))

    return redirect(url_for('admin_account'))


@app.route("/account/update_device_rego", methods=['POST'])
@login_required
@admin_login_required
def update_device_rego():
    if 'admin@cisco.com' == current_user.get_id():
        if request.form['submit'] == 'delete':
            mac = request.form.get("mac")
            app.logger.info("account_update_rego(): admin deleted mac {} registration.".format(mac))
            DB.delete_device(mac)
        elif request.form['submit'] == 'update':
            new_mac = request.form.get("new_mac")
            old_mac = request.form.get("mac")
            email = request.form.get("email")
            app.logger.info("account_update_rego(): device update old mac {} new mac{} email {}".format(old_mac, new_mac, email))
            if DB.delete_device(old_mac) > 0:
                hash_mac = CMX.hash_mac(new_mac)
                DB.add_device(hash_mac, email)
                app.logger.debug(
                    "account_update_rego(): updated email {} with new mac {}".format(email, new_mac))
            else:
                app.logger.info(
                    "account_update_rego(): tried to delete old mac {} failed.".format(old_mac))
        elif request.form['submit'] == 'new':
            email = request.form.get("email")
            ip = request.form.get("ip")
            new_mac = request.form.get("new_mac")
            new_hash_mac = request.form.get("new_hash_mac")
            if len(new_mac):
                hash_mac = CMX.hash_mac(new_mac)
                DB.add_device(hash_mac, email)
                app.logger.debug(
                    "account_update_rego(): add mac device {} to email {}".format(
                        new_mac, email))
            elif len(ip):
                mac = CMX.get_mac(ip)
                new_hash_mac = CMX.hash_mac(new_mac)
                DB.add_device(new_hash_mac, email)
                app.logger.debug(
                    "account_update_rego(): add device via ip {} {} to email {}".format(
                        new_mac, ip, email))
            elif len(new_hash_mac):
                DB.add_device(new_hash_mac, email)
                app.logger.debug(
                    "account_update_rego(): add device via hash mac {} to email {}".format(
                        new_hash_mac, email))
        else:
            app.logger.error(
                "account_update_rego(): unknown submit, should be delete or update, found {}".format(request.form['submit']))

    else:
        app.logger.debug("account_update_rego(): device update requested but not admin@cisco.com instead {}".format(current_user.get_id()))

    return redirect(url_for('admin_device'))


@app.route("/account/hash_mac", methods=['POST'])
@login_required
@admin_login_required
def check_mac_hash():
    real_mac = request.form.get("real_mac")
    hash_mac = request.form.get("hash_mac")
    app.logger.debug("check_mac_hash(): hashing mac {} compare with hash mac {}.".format(real_mac, hash_mac))
    verify_hash_mac = CMX.hash_mac(real_mac)
    if verify_hash_mac == hash_mac:
        app.logger.debug("check_mac_hash(): real mac verified as hash mac")
    else:
        app.logger.debug("check_mac_hash(): real mac NOT verified as hash mac")
    devices = DB.get_all_devices()


    return render_template("admin-devices.html", hash_mac=hash_mac, real_mac=real_mac, verify_hash_mac=verify_hash_mac, devices=devices)


@app.route("/account/get_mac", methods=['POST'])
@login_required
@admin_login_required
def get_mac():
    ip = request.form.get("lookup_ip")
    hash_mac = request.form.get("hash_mac")
    app.logger.debug("get_mac(): getting mac for ip {}.".format(ip))
    mac = CMX.get_mac(ip)
    hash_mac = CMX.hash_mac(mac)
    app.logger.debug("get_mac(): for ip {} got mac {} hash {}".format(ip, mac, hash_mac))
    owner = DB.get_device(hash_mac)
    app.logger.debug("get_mac(): for ip {} got owner {}".format(ip, owner))
    devices = DB.get_all_devices()

    return render_template("admin-devices.html", lookup_mac = mac, lookup_ip=ip, lookup_hash_mac=hash_mac, owner = owner, devices=devices)


@app.route("/login", methods=["POST"])
def login():
    form = RegistrationForm(request.form)
    email = request.form.get("email")
    password = request.form.get("password")
    app.logger.debug('login(): Login attempt from email {}'.format(email))
    stored_user = DB.get_user(email)
    if stored_user and PH.validate_password(password, stored_user['salt'], stored_user['hashed']):
        user = User(email)
        login_user(user, remember=True)
        app.logger.info('login(): Login attempt from email {} successful.'.format(email))
        if DB.is_admin(email):
            return redirect(url_for('admin_leaderboard'))
        else:
            return redirect(url_for('account'))
    else:
        app.logger.info('login(): Login attempt from email {} failed.'.format(email))
        return home("Login failed. Your email address or password is incorrect. To reset your password come to the Cisco on Cisco IT stand for help.")

    return home()


@app.route("/register", methods=["POST"])
def register():
    form = RegistrationForm(request.form)
    if form.validate():
        if DB.get_user(form.email.data):
            form.email.errors.append("Email address already registered")
            return render_template('home.html', registrationform=form)
        salt = PH.get_salt()
        hashed = PH.get_hash(form.password2.data + salt)
        nickname = form.nickname.data
        is_admin = False
        DB.add_user(form.email.data, salt, hashed, is_admin, nickname)
        user = User(form.email.data)
        login_user(user, remember=True)

        return redirect(url_for('account'))

    return render_template("home.html", registrationform=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/")
def home(error=None):
    registrationform = RegistrationForm()
    if error is None:
        return render_template("home.html", registrationform=registrationform)
    else:
        return render_template("home.html", registrationform=registrationform, onloadmessage=error)


@app.route("/user")
def user():
    return render_template("user.html")


@app.route("/learn-more")
def learn_more():
    return render_template("learn-more.html")


@app.route("/dashboard")
@login_required
def dashboard():
    if '@cisco.com' in current_user.get_id():
        top_devices = DB.get_num_devices(40, "%@cisco.com", False)
    else:
#        top_devices = DB.get_num_devices(10)
        date = datetime.datetime.now().strftime('%Y-%m-%d')
        top_devices = DB.get_num_devices_date(40, date)
    app.logger.debug('dashboard(): got {} number of devices to display'.format(len(top_devices)))

    return render_template("dashboard.html", devices=top_devices, user=current_user.get_id())


def render_account_devices(form, spark_added=False):
    ip = request.environ['REMOTE_ADDR']
    mac = CMX.get_mac(request.environ['REMOTE_ADDR'])
    app.logger.debug('render_account_devices(): ip {} and mac {}'.format(ip, mac))
    tracked_devices = DB.get_devices(current_user.get_id(), "", False)
    user = DB.get_user(current_user.get_id())

    return render_template("account.html", add_device_form=form, user=user, ip=ip, mac=mac,
                           tracked=tracked_devices, spark_added=spark_added)

@app.route("/account")
@login_required
def account():
    form = AddDevice(request.form)

    return render_account_devices(form)

@app.route("/account/join_spark", methods=["POST"])
@login_required
def account_add_spark():
    form = AddDevice(request.form)
    email = request.form.get("email")
    spark_added = SPARK.add_user(email)

    return render_account_devices(form, spark_added)


@app.route("/account/add_device", methods=["POST"])
@login_required
def account_add_device():
    form = AddDevice(request.form)
    if form.validate():
        new_mac = form.mac.data
        owner = DB.get_device(new_mac)
        number_registered_devices = DB.total_devices_registered(current_user.get_id())
        max_devices = app.config['MAX_REGISTERED_DEVICES']
        if not owner and number_registered_devices < max_devices:
            app.logger.info("account_add_device(): new mac {} with owner email {} requested."
                            .format(new_mac, current_user.get_id()))
            hash_mac = CMX.hash_mac(new_mac)
            DB.add_device(hash_mac, current_user.get_id())
        elif owner:
            app.logger.info("account_add_device(): user {} attempt to add device {} that already exists with {}."
                           .format(current_user.get_id(), new_mac, owner))
            form.mac.errors.append("Error: Device already registered.")
        elif number_registered_devices >= max_devices:
            app.logger.info("account_add_device(): user {} attempt to add device {} more than maximum allowed of {}."
                            .format(current_user.get_id(), new_mac, app.config['MAX_REGISTERED_DEVICES']))
            form.mac.errors.append("Error: Maximum number of {} devices already registered.".format(max_devices))
    else:
        app.logger.debug("account_add_device(): user {} form invalid {}".format(current_user.get_id(), form))


    return render_account_devices(form)


@app.route("/account/delete_device", methods=['POST'])
@login_required
def account_delete_device():
    mac = request.form.get("mac")
    email = current_user.get_id()
    app.logger.info("account_delete_device(): mac {} with email {} delete requested.".format(mac, email))
    DB.delete_device(mac)

    return redirect(url_for('account'))


@app.route('/notification', methods=['POST'])
@requires_auth
def cmx_notification():
    app.logger.debug('cmx_notification(): POST: received notification.')
    if request.json:
        try:
            mac = request.json['notifications'][0]['deviceId']
            new_distance_ft = request.json['notifications'][0]['moveDistanceInFt']
            x = request.json['notifications'][0]['locationCoordinate']['x']
            y = request.json['notifications'][0]['locationCoordinate']['y']
            new_floor_id = request.json['notifications'][0]['floorId']
            app.logger.debug('cmx_notification(): extracted mac {} distance-ft {} x {} y {} floor_id {}'.format(mac, new_distance_ft, x, y, new_floor_id))
            valid_notification = True
        except Exception as e:
            app.logger.debug('cmx_notification(): could not decode JSON notification. deviceId, move DistanceInFt, locationCoordinate floorId, Check CMX')
            valid_notification = False
        if valid_notification:
            new_point = Point((x,y), app)
            device_history = DB.get_device_points(mac)
            if 'floor_id' in device_history and 'point_1' in device_history and 'point_2' in device_history and \
                    'distance_1to2' in device_history and 'timer' in device_history:
                prev_floor_id = device_history['floor_id']
                prev_point_1 = Point(eval(device_history['point_1']), app)
                prev_point_2 = Point(eval(device_history['point_2']), app)
                distance_1to2 = device_history['distance_1to2']
                timer = device_history['timer']
            else:
                app.logger.debug('cmx_notification(): mac {} no device history {}.'.format(mac, device_history))
                prev_floor_id = 0
                prev_point_1 = Point((0,0), app)
                prev_point_2 = Point((0,0), app)
                distance_1to2 = 0.0
                timer = 86400
            new_distance = round(Distance(ft=new_distance_ft).m, 1)
            max_movement_distance = timer * app.config['MAX_MTRS_SEC']
            if new_distance > max_movement_distance:
                app.logger.debug('cmx_notification(): mac {} distance {} in {} secs exceeded maximum {}, setting to max.'.format(mac, new_distance, timer, max_movement_distance))
                new_distance = max_movement_distance
            if new_floor_id != prev_floor_id:
                app.logger.debug('cmx_notification(): mac {} changed floors from {} to {}.'.format(mac, prev_floor_id, new_floor_id))
                DB.add_device_dist(mac, 0.0, new_point, Point((0.0,0.0), app), new_floor_id, 0.0)
            else:
                app.logger.debug(
                    'cmx_notification(): mac {} same floor id {}.'.format(mac, new_floor_id))
                if prev_point_2.is_origin():
                    app.logger.debug(
                        'cmx_notification(): mac {} prev_point_2 at origin {}.'.format(mac, prev_point_2))
                    DB.add_device_dist(mac, 0.0, prev_point_1, new_point, new_floor_id, new_distance)
                else:
                    app.logger.debug('cmx_notification(): mac {} got at least 2 prev points on same floor prev_1 {} and prev_2 {}'.format(mac, prev_point_1, prev_point_2))
                    if prev_point_1.heading_away(prev_point_2, new_point, app.config['MAX_MOVING_ANGLE']):
                        total_distance = new_distance + distance_1to2
                        app.logger.debug(
                            'cmx_notification(): mac {} point moving away adding in total distance {}'.format(mac, total_distance))
                        DB.add_device_dist(mac, total_distance, prev_point_2, new_point, new_floor_id, new_distance)
                    else:
                        app.logger.debug(
                            'cmx_notification(): mac {} point circling, ignore new distance {}, just update points'.format(mac, new_distance))
                        DB.add_device_dist(mac, 0.0, prev_point_2, new_point, new_floor_id, new_distance)
    else:
        app.logger.info('Received non JSON data posted to app.')
        abort(400)
    return json.dumps(request.json)


@app.route('/notification/area', methods=['POST'])
@requires_auth
def cmx_zone_notification():
    app.logger.debug('cmx_zone_notification(): POST: received notification.')
    if request.json:
        zone_name = request.json['notifications'][0]['locationMapHierarchy']
        mac = request.json['notifications'][0]['deviceId']
        DB.add_zone(zone_name)
    else:
        app.logger.info('cmx_zone_notification(): Received non JSON data posted to app.')
        abort(400)
    return json.dumps(request.json)

### API Section
@app.route('/live/register_username', methods=['POST'])
@requires_auth
def api_register_username():
    reg_result = status.HTTP_200_OK
    app.logger.debug('api_register_username(): username registeration called.')
    if not (request.method == 'POST' and request.headers['Content-Type'] == 'application/json'):
        app.logger.error('api_register_username(): Not a post request or not application/json headers')
        response = {'error': 'Not a POST request or no application/json headers with username and ip'}
        reg_result = status.HTTP_400_BAD_REQUEST
    else:
        content = request.get_json()
        username = content['username']
        ip = content['ip']
        app.logger.debug('api_register_username(): POSTed username registeration called username {} ip {}.'.format(username, ip))
        if len(username) == 0 or username[0] == '@':
            app.logger.info('api_register_username(): username empty or first char a @ {} .'.format(username,))
            response = {'error': 'First character cannot be a @'}
            reg_result = status.HTTP_400_BAD_REQUEST
        else:
            if not '@' in username:
                email = username + "@cmxtrackyoursteps.com"
            else:
                email = username
            check_username_exist = DB.get_user(email)
            mac = CMX.get_mac(ip)
            if "00:00:00:00:00:00" in mac:
                response = {'error': 'Connect to #clus WiFi first',
                            'username': username, 'email': email, 'ip': ip}
                reg_result = status.HTTP_404_NOT_FOUND
            else:
                hash_mac = CMX.hash_mac(mac)
                device_owner = DB.get_username_from_mac(hash_mac)
                if check_username_exist and username == device_owner:
                    app.logger.debug(
                        'api_register_username(): username {} email {} mac {} hash_mac {} already registered'.format(
                            username, email, mac, hash_mac))
                    response = {'info': 'Username already registered with that mac, nothing to do',
                                'username': username, 'email': email,
                                'ip': ip, 'mac': mac}
                    reg_result = status.HTTP_200_OK
                elif check_username_exist:
                    response = {'error':'Username already registered', 'username': username, 'email':email}
                    reg_result = status.HTTP_409_CONFLICT
                elif len(device_owner) > 0:
                    error_msg = 'Device already registered with another username {}.'.format(device_owner)
                    response = {'error': error_msg, 'username': username,
                                'email': email,'mac': mac, 'hash_mac': hash_mac}
                    reg_result = status.HTTP_409_CONFLICT
                else:
                    salt = PH.get_salt()
                    hashed = PH.get_hash(app.config['API_USER_PASSWORD'] + salt)
                    result = DB.add_user(email, salt, hashed, False, username)
                    if result < 1:
                        response = {'error': 'Database error adding user', 'username': username, 'email': email, 'db_result': result}
                        reg_result = status.HTTP_500_INTERNAL_SERVER_ERROR
                        app.logger.error(
                            'api_register_username(): database error username {} db result {}.'.format(username, result))
                    else:
                        app.logger.debug('api_register_username(): username {} email {} registered db, result {}.'.format(username, email, result))
                        result = DB.add_device(hash_mac, email)
                        if  result < 1:
                            response = {'error': 'Database error adding device for user', 'username': username, 'email': email,
                                        'db_result': result}
                            reg_result = status.HTTP_500_INTERNAL_SERVER_ERROR
                            result = DB.delete_user(email)
                            app.logger.error(
                                'api_register_username(): database error adding device {} for username {} db result {}.'.format(
                                    hash_mac, username, result))
                        else:
                            response = {'success': 'Username added with device', 'username': username, 'email': email,
                                        'mac': mac, 'hash_mac': hash_mac, 'db_result': result}
                            reg_result = status.HTTP_201_CREATED

    js = json.dumps(response)

    return Response(js, status=reg_result, mimetype='application/json')

@app.route('/live/delete_username', methods=['POST'])
@requires_auth
def api_delete_username():
    reg_result = status.HTTP_200_OK
    app.logger.debug('api_delete_username(): username delete called.')
    if request.method == 'POST' and request.headers['Content-Type'] == 'application/json':
        content = request.get_json()
        if not 'username' in content.keys():
            response = {'error': 'Expecting keyname username to delete.', 'content': content}
            reg_result = status.HTTP_400_BAD_REQUEST
        else:
            username = content['username']
            app.logger.debug(
                'api_delete_username(): delete username {}'.format(username))
            if not '@' in username:
                email = username + "@cmxtrackyoursteps.com"
            else:
                email = username
            if not DB.get_user(email):
                response = {'error': 'Username not found', 'username': username, 'email': email}
                reg_result = status.HTTP_404_NOT_FOUND
            else:
                result = DB.delete_user(email)
                if result < 1:
                    response = {'error': 'Could not delete user from database', 'username': username, 'email': email}
                    reg_result = status.HTTP_500_INTERNAL_SERVER_ERROR
                else:
                    response = {'success': 'Username and associated devices deleted', 'username': username, 'email': email}
                    reg_result = status.HTTP_200_OK
    else:
        app.logger.error('api_delete_username(): did not get a POST or applicatin/json request.')

    js = json.dumps(response)

    return Response(js, status=reg_result, mimetype='application/json')

@app.route('/live/username_data', methods=['POST'])
@requires_auth
def api_username_data():
    reg_result = status.HTTP_200_OK
    app.logger.debug('api_username_data(): get user data called.')
    response = {'error': 'No data.'}
    if request.method == 'POST' and request.headers['Content-Type'] == 'application/json':
        content = request.get_json()
        if not 'username' in content.keys():
            response = {'error': 'Expecting key name username to get data for.', 'content': content}
            reg_result = status.HTTP_400_BAD_REQUEST
        else:
            username = content['username']
            if 'days' in content.keys():
                days = content['days']
            else:
                days = 5

            app.logger.debug(
                'api_username_data(): get data for username {} for {} days'.format(username, days))
            if not '@' in username:
                email = username + "@cmxtrackyoursteps.com"
            else:
                email = username
            if not DB.get_user(email):
                response = {'error': 'Username not found', 'username': username, 'email': email}
                reg_result = status.HTTP_404_NOT_FOUND
            else:
                devices = DB.get_devices_position(email)
                if len(devices) < 1:
                    response = {'error': 'Could not get device for username', 'username': username, 'email': email}
                    reg_result = status.HTTP_500_INTERNAL_SERVER_ERROR
                else:
                    result = []
                    for device in devices:
                        device_result = {}
                        if 'mtrs' in device.keys():
                            device_result['username'] = username
                            device_result['mac'] = device['mac']
                            device_result['total_kilometres'] = round(Distance(metre=device['mtrs']).km, 3)
                            device_result['total_miles'] = round(Distance(metre=device['mtrs']).mi, 3)
                            device_result['place'] = device['place']
                            if 'mac' in device.keys():
                                distance_days = DB.get_device_days(device['mac'], days)
                                dst_day= []
                                for day in distance_days:
                                    dst_day.append({'date':'{:%m/%d/%Y}'.format(day['date']),
                                                    'km': round(Distance(metre=day['mtrs']).km,3),
                                                    'miles': round(Distance(metre=day['mtrs']).mi,3)})
                                device_result['distance_day'] = dst_day
                        result.append(device_result)
                    response = result
                    reg_result = status.HTTP_200_OK
    #print(response)
    js = json.dumps(response, sort_keys=True)

    return Response(js, status=reg_result, mimetype='application/json')


@app.route('/live/leaderboard', methods=['POST'])
@requires_auth
def api_leaderboard():
    reg_result = status.HTTP_200_OK
    app.logger.debug('api_leaderboard(): get leader board data called.')
    response = {'error': 'No data to display for the leader board.'}
    if request.method == 'POST' and request.headers['Content-Type'] == 'application/json':
        content = request.get_json()
        if 'number_leaders' in content.keys():
            number_leaders = content['number_leaders']
        else:
            number_leaders = 5
        app.logger.debug('api_leaderboard(): get data for {} of leaders'.format(number_leaders))
        total_result = {}
        total = DB.get_total_devices()
        if total > 0:
            total_result['total_kilometres'] = round(Distance(metre=total).km, 1)
            total_result['total_miles'] = round(Distance(metre=total).mi, 1)
        else:
            total_result['total_kilometres'] = 0.0
            total_result['total_miles'] = 0.0
        result = []
        enteries = DB.get_leaderboard(number_leaders)
        for entry in enteries:
            result.append({'place': entry['place'],
                           'username': entry['username'],
                           'kilometres': round(Distance(metre=entry['mtrs']).km,1),
                           'miles': round(Distance(metre=entry['mtrs']).mi, 1)})
        total_result['leaders'] = result
        response = total_result
        reg_result = status.HTTP_200_OK
    js = json.dumps(response, sort_keys=True)

    return Response(js, status=reg_result, mimetype='application/json')


@app.route('/live/ip_username', methods=['POST'])
@requires_auth
def api_ip_username():
    reg_result = status.HTTP_204_NO_CONTENT
    app.logger.debug('api_ip_username(): get username from ip, check if device registered.')
    response = {'error': 'Devie not registered.'}
    if request.method == 'POST' and request.headers['Content-Type'] == 'application/json':
        content = request.get_json()
        if not 'ip' in content.keys():
            app.logger.debug('api_ip_username(): missing ip variable in json data.')
            reg_result = status.HTTP_405_METHOD_NOT_ALLOWED
        else:
            ip = content['ip']
            app.logger.debug('api_ip_username(): check if ip {} has been registered'.format(ip))
            mac = CMX.get_mac(ip)
            if "00:00:00:00:00:00" in mac:
                app.logger.debug('api_ip_username(): no mac found from CMX.')
                reg_result = status.HTTP_404_NOT_FOUND
                response = {'error': 'IP not found on CMX.'}
            else:
                app.logger.debug('api_ip_username(): got mac {} for ip {} has been registered'.format(mac, ip))
                hash_mac = CMX.hash_mac(mac)
                username = DB.get_username_from_mac(hash_mac)
                if len(username) <= 0:
                    reg_result = status.HTTP_204_NO_CONTENT
                    response = {'ip': ip, 'username': username, 'hash_mac': hash_mac}
                else:
                    reg_result = status.HTTP_200_OK
                    response = {'ip': ip, 'username': username, 'hash_mac': hash_mac}

    js = json.dumps(response, sort_keys=True)

    return Response(js, status=reg_result, mimetype='application/json')


###


@app.teardown_appcontext
def close_db(error):
    DB.close_db()


if __name__ == '__main__':
    app.run(port=5000, debug=True)
