from ciscosparkapi import CiscoSparkAPI, SparkApiError, ciscosparkapiException

class SparkHelper:

    def __init__(self, app):
        self.app = app
        self.roomId = app.config['SPARK_ROOM_ID']
        try:
            self.api = CiscoSparkAPI(access_token=app.config['SPARK_BOT_TOKEN'])
        except ciscosparkapiException as e:
            self.app.logger.info("SparkHelper(): error connecting to CiscoSparkAPI: %s", e)
            self.api = None


    def add_user(self, email):

        in_room = False
        if self.api:
            try:
                members = list(self.api.memberships.list(personEmail=email, roomId=self.roomId))
                if len(members) > 0:
                    self.app.logger.debug(
                        "add_user(): user {} already in room with id {}".format(email, self.roomId))
                    in_room = True
                    response = 0
            except SparkApiError as e:
                self.app.logger.info("add_user(): Error with CiscoSparkAPI when testing if user in room ", e)
                response = 0
            if not in_room:
                try:
                    membership = self.api.memberships.create(personEmail=email, roomId=self.roomId)
                    response = membership.id
                    self.app.logger.debug("add_user(): user {} successfully added to room with id {}".format(email, response))
                except SparkApiError as e:
                    self.app.logger.info("add_user(): User not added to room. Error connecting to CiscoSparkAPI: %s", e)
                    response = 0
        else:
            self.app.logger.info("add_user(): api not initialised")
            response = 0


        return response


    def delete_user(self, email):

        response = True
        members = []

        if self.api:
            try:
                members = list(self.api.memberships.list(personEmail=email, roomId=self.roomId))
            except SparkApiError as e:
                self.app.logger.info("delete_user(): Error with CiscoSparkAPI ", e)
                response = False

            if len(members) == 0:
                self.app.logger.info("delete_user(): Could not find user {} in room to delete".format(email))
                response = False
            elif len(members) >= 1:
                if len(members) > 1:
                    self.app.logger.info(
                        "delete_user(): got too many id's in room for email {} in room. Will delete first one only".format(
                            email))
                    response = False
                user_id = members[0].id
                try:
                    self.api.memberships.delete(user_id)
                    self.app.logger.debug("delete_user(): deleted user {} from room".format(email))
                except SparkApiError as e:
                    self.app.logger.info("delete_user(): Error with CiscoSparkAPI ", e)
                    response = False
        else:
            self.app.logger.info("delete_user(): api not initialised")
            response = False

        return response


    def post_room(self, message):

        response = True
        try:
            api_response = self.api.messages.create(roomId=self.roomId, markdown = message)
            self.app.logger.debug(
                    "post_room(): response {}.".format(api_response))
        except SparkApiError as e:
            self.app.logger.info("post_room(): request to Spark failed: %s", e)
            response = False

        return True
