import psycopg2
import psycopg2.extras
from flask import g


class DBHelper:
    def __init__(self, app):
        self.app = app
        if app.config['HOST'] and app.config['DBNAME'] and app.config['DB_USERNAME'] and app.config['DB_PASSWORD']:
            self.host = app.config['HOST']
            self.dbname = app.config['DBNAME']
            self.db_username = app.config['DB_USERNAME']
            self.db_password = app.config['DB_PASSWORD']
        else:
            self.app.logger.error("DBHelper init(): ERROR config.ini missing HOST, DBNAME, DB_USERNAME, DB_PASSWORD")

    def get_db(self):
        """Opens a new database connection if there is none yet for the
        current application context.
        """
        if not hasattr(g, 'db_conn'):
            try:
                g.db_conn = psycopg2.connect(host=self.host, dbname=self.dbname,
                                             user=self.db_username, password=self.db_password)
                self.app.logger.debug("getdb(): connection to db {} succeeded".format(self.host))
            except Exception as e:
                self.app.logger.error("get_db(): connection to db failed: %s", e)
                g.db_conn = None

        return g.db_conn


    def get_user(self, email):
        user = None
        self.app.logger.debug("get_user(): called with email {}".format(email))
        conn = self.get_db()
        if conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            try:
                cursor.execute('''SELECT * FROM users WHERE email = %s''', (email,))
                user = cursor.fetchone()
                self.app.logger.debug("get_user(): email {} found in db {}".format(email, user))
            except Exception as e:
                self.app.logger.warning("get_user(): db connection failed, %s", e)

        return user


    def get_device(self, mac):
        user = None
        self.app.logger.debug("get_device(): called with mac {}".format(mac))
        conn = self.get_db()
        if conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            try:
                cursor.execute('''SELECT owner FROM devices WHERE mac =%s''', (mac,))
                user = cursor.fetchone()
                self.app.logger.debug("get_device(): owner {} found in db for mac".format(user,mac))
            except Exception as e:
                self.app.logger.warning("get_user(): db connection failed, %s", e)

        return user


    def get_all_users(self, email_search=""):
        users = None
        self.app.logger.debug("get_all_users(): called with search str {}".format(email_search))
        conn = self.get_db()
        search_str = "%"+email_search+"%"
        if conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            try:
                cursor.execute('''
                              SELECT email, nickname, admin 
                              FROM users 
                              WHERE email LIKE %s 
                              ORDER BY email;
                              ''', (search_str,))
                users = cursor.fetchall()
                self.app.logger.debug("get_all_users(): got {} of records".format(cursor.rowcount))
            except Exception as e:
                self.app.logger.warning("get_all_users(): db connection failed, %s", e)
        return users


    def add_user(self, email, salt, hashed, is_admin, nickname):
        self.app.logger.debug("add_user(): called with email {}".format(email))
        conn = self.get_db()
        result = 0
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute('''INSERT INTO users (email, salt, hashed, admin, nickname) VALUES (%s, %s, %s, %s, %s)''', (email, salt, hashed, is_admin, nickname))
                conn.commit()
                result = cursor.rowcount
                self.app.logger.debug("add_user(): added to db, {} number of devices added.".format(cursor.rowcount))
            except Exception as e:
                self.app.logger.warning("add_user(): db connection failed, %s", e)
            self.update_count(1, 0, 0)
        return result


    def reset_user_password(self, email, salt, hashed):
        self.app.logger.debug("reset_user_password(): called with email {}".format(email))
        conn = self.get_db()
        result = 0
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute('''
                          UPDATE users 
                          SET salt = %s, hashed = %s 
                          WHERE email = %s;
                          ''', (salt, hashed, email))
                conn.commit()
                result = cursor.rowcount
                self.app.logger.debug("reset_user_password(): added to db, {} number of devices added.".format(cursor.rowcount))
            except Exception as e:
                self.app.logger.warning("reset_user_password(): db connection failed, %s", e)
        return result


    def update_user_name(self, email, nickname):
        self.app.logger.debug("update_user_name(): called with email {} name {}".format(email, nickname))
        conn = self.get_db()
        result = 0
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute('''
                          UPDATE users 
                          SET nickname = %s 
                          WHERE email = %s;
                          ''', (nickname, email))
                conn.commit()
                result = cursor.rowcount
                self.app.logger.debug("update_user_name()(): updated, {} users.".format(cursor.rowcount))
            except Exception as e:
                self.app.logger.warning("update_user_name()(): db connection failed, %s", e)
        return result


    def delete_user(self, email):
        conn = self.get_db()
        result = 0
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute('''DELETE FROM devices WHERE owner = %s;''', (email,))
                cursor.execute('''DELETE FROM users WHERE email = %s;''', (email,))
                conn.commit()
                result = cursor.rowcount
            except Exception as e:
                self.app.logger.warning("delete_user(): db connection failed, %s", e)

            self.update_count(-1, 0, 0)
        return result

    def make_user_admin(self, email, is_admin):
        conn = self.get_db()
        result = 0
        if isinstance(is_admin, bool):
            self.app.logger.debug("make_user_admin(): setting user {} admin status to {}".format(email, is_admin))
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute('''UPDATE users SET admin = %s WHERE email = %s;''', (is_admin, email))
                    conn.commit()
                    result = cursor.rowcount
                except Exception as e:
                    self.app.logger.warning("make_user_admin(): db connection failed, %s", e)
        else:
            self.app.logger.warning("make_user_admin(): is_admin {} is not of type boolean, needs to be True or False".format(is_admin))

        return result


    def is_admin(self, email):
        self.app.logger.debug("is_admin(): called with email {}".format(email))
        conn = self.get_db()
        admin = False
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''SELECT admin FROM users WHERE email = %s''', (email,))
                admin = cursor.fetchone()[0]
                self.app.logger.debug("is_admin(): email {} found in db with admin status of {}".format(email, admin))
            except Exception as e:
                self.app.logger.warning("is_admin(): db connection failed, %s", e)

        return admin


    def get_devices(self, email, domain="%@cisco.com", exclude=True):
        self.app.logger.debug("get_devices(): called with email {}".format(email))
        conn = self.get_db()
        devices = []
        if conn:
            try:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                if exclude:
                    cursor.execute('''
                                SELECT place, mac, mtrs, owner, nickname
                                FROM (
                                SELECT 
                                ROW_NUMBER () OVER (ORDER BY COALESCE(distance.mtrs, 0.0) DESC) AS place,
                                devices.mac AS mac, 
                                COALESCE(distance.mtrs, 0.0) AS mtrs,
                                devices.owner AS owner,
                                users.nickname AS nickname
                                FROM distance
                                RIGHT JOIN devices ON devices.mac = distance.mac
                                INNER JOIN users ON devices.owner = users.email
                                WHERE devices.owner NOT LIKE %s
                                ) sub
                                WHERE owner = %s''', (domain, email))
                else:
                    cursor.execute('''
                                SELECT place, mac, mtrs, owner, nickname
                                FROM (
                                SELECT 
                                ROW_NUMBER () OVER (ORDER BY COALESCE(distance.mtrs, 0.0) DESC) AS place,
                                devices.mac AS mac, 
                                COALESCE(distance.mtrs, 0.0) AS mtrs,
                                devices.owner AS owner,
                                users.nickname AS nickname
                                FROM distance
                                RIGHT JOIN devices ON devices.mac = distance.mac
                                INNER JOIN users ON devices.owner = users.email
                                ) sub
                                WHERE owner = %s''', (email,))
                devices = cursor.fetchall()
                self.app.logger.debug("get_devices(): got {} number of devices".format(len(devices)))
            except Exception as e:
                self.app.logger.warning("get_devices(): db connection failed, %s", e)

        return devices

    def get_username_from_mac(self, hash_mac):
        username = ""
        self.app.logger.debug("get_username_from_mac(): called with mac {}".format(hash_mac))
        conn = self.get_db()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''SELECT users.nickname FROM devices INNER JOIN users ON devices.owner = users.email WHERE mac = %s''', (hash_mac,))
                owner = cursor.fetchone()
                if cursor.rowcount <= 0:
                    self.app.logger.debug("get_username_from_mac(): no details returned for hash mac {}".format(hash_mac))
                    username = ""
                else:
                    self.app.logger.debug("get_username_from_mac(): got owner {}".format(owner))
                    username = owner[0]
            except Exception as e:
                self.app.logger.warning("get_username_from_mac(): db connection failed, %s", e)

        return username


    def get_all_devices(self, search=""):
        self.app.logger.debug("get_all_devices(): called.")
        conn = self.get_db()
        devices = []
        search_str = "%" + search + "%"
        if conn:
            try:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute('''
                            SELECT place, mac, mtrs, owner, nickname
                            FROM (
                            SELECT 
                            ROW_NUMBER () OVER (ORDER BY COALESCE(distance.mtrs, 0.0) DESC) AS place,
                            devices.mac AS mac, 
                            COALESCE(distance.mtrs, 0.0) AS mtrs,
                            devices.owner AS owner,
                            users.nickname AS nickname
                            FROM distance
                            RIGHT JOIN devices ON devices.mac = distance.mac
                            INNER JOIN users ON devices.owner = users.email
                            ) sub
                            WHERE owner LIKE %s''', (search_str,))
                devices = cursor.fetchall()
                self.app.logger.debug("get_all_devices(): got {} number of devices".format(len(devices)))
            except Exception as e:
                self.app.logger.warning("get_all_devices(): db connection failed, %s", e)

        return devices


    def get_total_devices(self):
        self.app.logger.debug("get_total_devices(): called.")
        conn = self.get_db()
        total = 0.0
        result = []
        if conn:
            try:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute('''
                                SELECT ROUND(SUM(mtrs)::numeric,1) AS total
                                FROM distance
                                INNER JOIN devices ON devices.mac = distance.mac;
                            ''')
                result = cursor.fetchone()
                self.app.logger.debug("et_total_devices(): got {} total".format(total))
            except Exception as e:
                self.app.logger.warning("et_total_devices(): db connection failed, %s", e)

        if 'total' in result.keys():
            total = result['total']

        return total


    def get_select_devices(self, domain="%@cisco.com", include=True):
        self.app.logger.debug("get_all_devices(): called.")
        conn = self.get_db()
        devices = []
        if conn:
            try:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                if include:
                    cursor.execute('''
                                SELECT place, mac, mtrs, owner, nickname
                                FROM (
                                SELECT 
                                ROW_NUMBER () OVER (ORDER BY COALESCE(distance.mtrs, 0.0) DESC) AS place,
                                devices.mac AS mac, 
                                COALESCE(distance.mtrs, 0.0) AS mtrs,
                                devices.owner AS owner,
                                users.nickname AS nickname
                                FROM distance
                                RIGHT JOIN devices ON devices.mac = distance.mac
                                INNER JOIN users ON devices.owner = users.email
                                ) sub
                                WHERE owner LIKE %s''', (domain,))
                else:
                    cursor.execute('''
                                 SELECT place, mac, mtrs, owner, nickname
                                 FROM (
                                 SELECT 
                                 ROW_NUMBER () OVER (ORDER BY COALESCE(distance.mtrs, 0.0) DESC) AS place,
                                 devices.mac AS mac, 
                                 COALESCE(distance.mtrs, 0.0) AS mtrs,
                                 devices.owner AS owner,
                                 users.nickname AS nickname
                                 FROM distance
                                 RIGHT JOIN devices ON devices.mac = distance.mac
                                 INNER JOIN users ON devices.owner = users.email
                                 ) sub
                                 WHERE owner NOT LIKE '%@%s';''', (domain,))
                devices = cursor.fetchall()
                self.app.logger.debug("get_all_devices(): got {} number of devices".format(len(devices)))
            except Exception as e:
                self.app.logger.warning("get_all_devices(): db connection failed, %s", e)

        return devices


    def get_user_distance(self, email):
        self.app.logger.debug("get_user_distance(): called with email {}".format(email))
        conn = self.get_db()
        user_distance = []
        if conn:
            try:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute('''
                SELECT devices.owner AS owner, users.nickname AS nickname, distance.mtrs AS distance
                FROM devices
                INNER JOIN distance ON devices.mac = distance.mac
                INNER JOIN users ON devices.owner = users.email
                WHERE devices.owner = %s''', (email,))
                user_distance = cursor.fetchall()
                self.app.logger.debug("get_user_distance(): got {} number of devices".format(len(user_distance)))
            except Exception as e:
                self.app.logger.warning("get_user_distance(): db connection failed, %s", e)

        return user_distance


    def get_num_devices_date(self, number, date, domain='%@cisco.com', exclude=True):
        self.app.logger.debug("get_num_devices_date(): called with number {} date".format(number, date))
        conn = self.get_db()
        user_distance = []
        if conn:
            try:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                if exclude:
                    cursor.execute('''
                                SELECT devices.owner, users.nickname, distance_history.mtrs, devices.mac, distance_history.time::date
                                FROM devices
                                INNER JOIN distance_history ON devices.mac = distance_history.mac
                                INNER JOIN users ON devices.owner = users.email
                                WHERE  distance_history.time = %s 
                                  AND owner NOT LIKE %s
                                ORDER BY mtrs DESC LIMIT %s;''', (date, domain, number))
                else:
                    cursor.execute('''
                                SELECT devices.owner, users.nickname, distance_history.mtrs, devices.mac, distance_history.time::date
                                FROM devices
                                INNER JOIN distance_history ON devices.mac = distance_history.mac
                                INNER JOIN users ON devices.owner = users.email
                                WHERE  distance_history.time = %s 
                                ORDER BY mtrs DESC LIMIT %s;''', (date,  number))
                user_distance = cursor.fetchall()
                self.app.logger.debug("get_num_devices_date(): got {} number of devices".format(len(user_distance)))
            except Exception as e:
                self.app.logger.warning("get_num_devices_date(): db connection failed, %s", e)

        return user_distance



    def get_devices_position(self, email):
        self.app.logger.debug("get_devices_position(): called with email {}".format(email))
        conn = self.get_db()
        devices = []
        if conn:
            try:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute('''
                        SELECT nickname AS username, place, mac, mtrs 
                        FROM (
                        SELECT 
                        ROW_NUMBER () OVER (ORDER BY COALESCE(distance.mtrs, 0.0) DESC) AS place,
                        devices.mac AS mac, 
                        COALESCE(distance.mtrs, 0.0) AS mtrs,
                        devices.owner AS owner,
                        users.nickname AS nickname
                        FROM distance
                        RIGHT JOIN devices ON devices.mac = distance.mac
                        INNER JOIN users ON devices.owner = users.email
                        ) sub
                        WHERE owner = %s''', (email,))
                devices = cursor.fetchall()
                self.app.logger.debug("get_devices_position(): got {} number of devices".format(len(devices)))
            except Exception as e:
                self.app.logger.warning("get_devices_position(): db connection failed, %s", e)

        return devices


    def get_device_days(self, mac, days=5):
        self.app.logger.debug("get_device_days(): called with mac {} for {} days".format(mac, days))
        conn = self.get_db()
        device_distance = []
        if conn:
            try:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute('''
                            SELECT time::date as date, mtrs 
                            FROM distance_history
                            WHERE  mac = %s
                             AND time > current_date - interval '%s' day
                            ORDER BY time ASC;''', (mac, days))
                device_distance = cursor.fetchall()
                self.app.logger.debug("get_device_days(): got {} number of d".format(len(device_distance)))
            except Exception as e:
                self.app.logger.warning("get_device_dayse(): db connection failed, %s", e)

        return device_distance

    def get_leaderboard(self, number):
        self.app.logger.debug("get_leaderboard(): called with number of devices = {}".format(number))
        conn = self.get_db()
        entries = []
        if conn:
            try:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute('''
                        SELECT ROW_NUMBER () OVER (ORDER BY COALESCE(distance.mtrs, 0.0) DESC) AS place, 
                        users.nickname AS username, ROUND(distance.mtrs::numeric, 1) AS mtrs
                        FROM devices
                        INNER JOIN distance ON devices.mac = distance.mac
                        INNER JOIN users ON devices.owner = users.email
                        ORDER BY mtrs DESC LIMIT %s''', (number,))
                entries = cursor.fetchall()
                self.app.logger.debug("get_leaderboard(): got {} number of enteries".format(cursor.rowcount))
            except Exception as e:
                self.app.logger.warning("get_leaderboard(): db connection failed, %s", e)

        return entries



    def get_num_devices(self, number, domain='%@cisco.com', exclude=True):
        self.app.logger.debug("get_num_devices(): called with number of devices = {}".format(number))
        conn = self.get_db()
        entries = []
        if conn:
            try:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                if exclude:
                    cursor.execute('''
                                SELECT devices.owner, users.nickname, distance.mtrs, devices.mac
                                FROM devices
                                INNER JOIN distance ON devices.mac = distance.mac
                                INNER JOIN users ON devices.owner = users.email
                                WHERE devices.owner NOT LIKE %s
                                ORDER BY mtrs DESC LIMIT %s''', (domain, number))
                else:
                    cursor.execute('''
                                SELECT devices.owner, users.nickname, distance.mtrs, devices.mac
                                FROM devices
                                INNER JOIN distance ON devices.mac = distance.mac
                                INNER JOIN users ON devices.owner = users.email
                                ORDER BY mtrs DESC LIMIT %s''', (number,))
                entries = cursor.fetchall()
                self.app.logger.debug("get_user_distance(): got {} number of devices".format(cursor.rowcount))
            except Exception as e:
                self.app.logger.warning("get_num_devices(): db connection failed, %s", e)

        return entries

    def total_devices(self):
        self.app.logger.debug("total_devices(): called.")
        conn = self.get_db()
        num_devices = 0
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute('''SELECT COUNT(*) FROM distance''')
                num_devices = cursor.fetchall()[0][0]
                self.app.logger.debug("total_devices: got {} number of devices".format(num_devices))
            except Exception as e:
                self.app.logger.warning("total_devices(): db connection failed, %s", e)

        return num_devices


    def total_devices_registered(self, email):
        self.app.logger.debug("total_devices_registered(): called.")
        conn = self.get_db()
        num_devices = 0
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute('''SELECT COUNT(*) FROM devices WHERE owner = %s''',(email,))
                num_devices = cursor.fetchall()[0][0]
                self.app.logger.debug("total_devices_registered: got {} number of devices".format(num_devices))
            except Exception as e:
                self.app.logger.warning("total_devices(): db connection failed, %s", e)

        return num_devices


    def total_users(self):
        self.app.logger.debug("total_users(): called.")
        conn = self.get_db()
        num_users = 0
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute('''SELECT COUNT(*) FROM users''')
                num_users = cursor.fetchall()[0][0]
                self.app.logger.debug("total_users: got {} number of devices".format(num_users))
            except Exception as e:
                self.app.logger.warning("total_users(): db connection failed, %s", e)

        return num_users


    def total_tracked_devices(self):
        self.app.logger.debug("total_tracked_devices(): called.")
        conn = self.get_db()
        num_devices = 0
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute('''SELECT COUNT(*) FROM devices''')
                num_devices = cursor.fetchall()[0][0]
                self.app.logger.debug("total_tracked_devices: got {} number of devices".format(num_devices))
            except Exception as e:
                self.app.logger.warning("total_tracked_devices(): db connection failed, %s", e)

        return num_devices


    def add_device(self, mac, email):
        print("Add_device ", mac)
        conn = self.get_db()
        result = 0
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute('''
                INSERT INTO devices (mac, owner) VALUES (%s, %s) ON CONFLICT(mac) DO NOTHING;
                ''', (mac, email))
                conn.commit()
                result = cursor.rowcount
            except Exception as e:
                self.app.logger.warning("add_device(): db connection failed, %s", e)
            self.update_count(0, 1, 0)
        return result

    def delete_device(self, mac):
        conn = self.get_db()
        result = 0
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute('''DELETE FROM devices WHERE mac = %s;''', (mac,))
                conn.commit()
                result = cursor.rowcount
            except Exception as e:
                self.app.logger.warning("delete_device(): db connection failed, %s", e)

            self.update_count(0,-1,0)
        return result

    def add_device_dist(self, mac, distance, point_1, point_2, floor_id, distance_1to2):
        conn = self.get_db()
        result = 0
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute('''
                INSERT INTO distance(mac, mtrs, point_1, point_2, floor_id, distance_1to2, timer) VALUES(%s, %s, %s, %s, %s, %s, current_timestamp)
                ON CONFLICT(mac) DO 
                UPDATE SET mtrs = distance.mtrs + %s,
                point_1 = %s, point_2 = %s, floor_id = %s, distance_1to2 = %s, timer = current_timestamp;
                ''', (mac, distance, str(point_1), str(point_2), floor_id, distance_1to2, distance, str(point_1), str(point_2), floor_id, distance_1to2))
                cursor.execute('''INSERT INTO distance_history(time, mac, mtrs) 
                VALUES(date_trunc('day', current_timestamp), %s, %s)
                ON CONFLICT(time, mac) DO 
                UPDATE SET mtrs = distance_history.mtrs + %s;''', (mac, 0, distance))
                conn.commit()
            except Exception as e:
                self.app.logger.warning("add_device_dist(): db connection failed, %s", e)
            self.update_count(0,0,1)

        return result

    def get_device_points(self, mac):
        conn = self.get_db()
        self.app.logger.debug("get_device_points(): get details for mac {}".format(mac))
        if conn:
            try:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute('''
                      SELECT COALESCE(point_1, '(0,0)') AS point_1, 
                      COALESCE(point_2, '(0,0)') AS point_2,
                      COALESCE(floor_id, 0) AS floor_id,
                      COALESCE(distance_1to2, 0.0) AS distance_1to2,
                      ROUND(EXTRACT (EPOCH FROM current_timestamp) - EXTRACT(EPOCH FROM COALESCE(timer, current_timestamp - interval '1' day))) AS timer
                      FROM distance 
                      WHERE mac =%s;
                      ''', (mac,))
                conn.commit()
                device = cursor.fetchone()
                self.app.logger.debug("get_device_points(): got details {}".format(device))
                if device is None:
                    self.app.logger.debug("get_device_points(): no details returned, setting defaults {}".format(mac))
                    device = {'floor_id':0, 'point_1':'(0,0)', 'point_2':'(0,0)', 'distance_1to2':0.0}
            except Exception as e:
                self.app.logger.warning("get_device_points(): db connection failed, %s", e)

        return device


    def update_count(self, user, device, notification):
        conn = self.get_db()
        result = 0
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute('''
                        INSERT INTO count
                        (time, user_count, device_count, notification_count) 
                        VALUES (date_trunc('minute', CURRENT_TIMESTAMP), %s, %s, %s)
                        ON CONFLICT (time) 
                        DO UPDATE SET
                        user_count = count.user_count + %s,
                        device_count = count.device_count + %s,
                        notification_count = count.notification_count + %s;
                        ''', (user, device, notification, user, device, notification))
                conn.commit()
                result = cursor.rowcount
            except Exception as e:
                self.app.logger.warning("update_count(): db connection failed, %s", e)
        return result


    def total_counts(self, number_records=25):
        self.app.logger.debug("total_counts(): called.")
        conn = self.get_db()
        results = []
        if conn:
            try:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute('''
                        SELECT time,
                        SUM(user_count) OVER (ORDER BY time) user_count,
                        SUM(device_count) OVER (ORDER BY time) device_count,
                        notification_count
                        FROM count
                        ORDER BY time DESC
                        LIMIT %s;''', (number_records,))
                results = cursor.fetchall()
                self.app.logger.debug("total_counts: got {} number of records".format(cursor.rowcount))
            except Exception as e:
                self.app.logger.warning("total_counts(): db connection failed, %s", e)

        return results

    def add_zone(self, zone_name):
        conn = self.get_db()
        result = 0
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute('''INSERT INTO zone(time, name, count) 
                VALUES(date_trunc('minute', current_timestamp), %s, 1)
                ON CONFLICT(time, name) DO 
                UPDATE SET count = zone.count + 1;''', (zone_name,))
                conn.commit()
                result = cursor.rowcount
            except Exception as e:
                self.app.logger.warning("add_zone(): db connection failed, %s", e)
            self.update_count(0,0,1)

        return result


    def close_db(self):
        conn = self.get_db()
        try:
            conn.close()
        except Exception as e:
            self.app.logger.warning("close_db(): db connection failed, %s", e)
