# CMX Track your steps back-end

## Introduction

The CMX Track Your Steps back-end (TYS) provides the distance and steps data used for the Cisco Live events application. The application accepts northbound distance notifications from the Cisco live CMX, which it stores, computes and summarises client data via a standard REST API. The application is to integrate with a front-end system that accepts client connections from their mobile phones and makes the appropriate API calls to retrieve relevant data that is required.

## Architecture

TYS comprises of a number of components:

1. **Mobile clients** : wireless mobile clients that connect to the WiFi network
2. **Wireless LAN Controller (WLC):** provides the control point for the AP&#39;s as well as collecting client data from the AP&#39;s
3. **CMX:** Connected mobile experience software that communicates with the WLC with NMSP to extract client data from the AP&#39;s.
4. **Apache web server (back-end):** accepts incoming HTTP/HTTPS connections from the CMX and front-end application. Routes the incoming connection to the Apache module, mod\_wsgi, which runs a Python script.
5. **CMX.py** : Back-end Python script which uses a Flask framework to route incoming web requests to the appropriate Python function. Each function performs a specific task depending on what URL that it hits on the Apache server.
6. **PostgreSQL:** RDMS database which stores the data from CMX and makes it readily available to client requests via API calls.
7. **Front-end webserver:** web server that handles the incoming client requests, validates any form data and returns dynamic web pages based on content extracted from the back-end via the API&#39;s.

## Back-end API

A REST API was developed to provide an easy integration into the front-end application.

### Summary of error messages from API

To assist with developing the workflow for landing pages for the front, the following table summarises the error messages for each API. Typically, these error messages inform users of any potential problems.

| **API** | **Name** | **Text** |
| --- | --- | --- |
| register\_username | error | Username already registered |
|   | error | Database error adding user |
|   | error | Username already registered with that mac, nothing to do |
|   | error | Device already registered with another username. |
|   | error | Connect to #clus WiFi first |
|   | error | Not a POST request or no application/json headers with username and ip |
|   | success | Username added with device |
| delete\_username | error | Expecting keyname username to delete. |
|   | error | Username not found |
|   | error | Could not delete user from database |
|   | success | Username and associated devices deleted |
| username\_data | error | No data |
|   | error | Expecting key name username to get data for. |
|   | error | Username not found |
|   | error | Could not get device for username |
| api\_leaderboard | error | No data to display for the leader board |

### Back-end API

The back-end CMX.py Python script provides a number of API calls to Create, Update, Delete data for the clients.

**API-0: Authentication**

**Description:**

All API requests must include authentication. It use a simple base64 encoded username and password as below and this ensures that only valid requests are processed.

**API-1: Register username**

**Description**

Register a username into the back end database. The provided client IP address is used to find its mac address on the CMX. The mac address is then associated to the username. This will mean a user only needs to provide their username for all new requests for data.

**URI**

/live/register\_username

**HTTP Method**

POST

**Content Type**

application/json

| **Name** | **Required** | **Default** | **Type** | **Location** | **Description** |
| --- | --- | --- | --- | --- | --- |
| username | Y | - | String | body | Unique username string |
| ip | Y | - | String | body | Clients internal wireless ip address |

| **Status Code** | **Description** |
| --- | --- |
| HTTP\_200\_OK | Username already has been registered with that ip address/mac address. Nothing to do. |
| HTTP\_201\_CREATED | IP address found on CMX and username has been registered successfully. |
| HTTP\_400\_BAD\_REQUEST | Username not a string, or ip address not formatted correctly e.g. 1.1.1.1 |
| HTTP\_401\_UNAUTHORIZED | Authentication error. |
| HTTP\_404\_NOT\_FOUND | IP address not found on CMX and no mac address could be registered with the username |
| HTTP\_409\_CONFLICT | Duplicate username. Need to create a unique username. |
| HTTP\_500\_INTERNAL\_SERVER\_ERROR | Something went wrong on the stepper\_backend app. |

**API-2: Delete User**

**Description**

Delete a username in the database. The data associated with that mac address will remain in the so if the user registers again the data will still be there.

**URI**

/live/delete\_username

**HTTP Method**

POST

**Content Type**

application/json

| **Name** | **Required** | **Default** | **Type** | **Location** | **Description** |
| --- | --- | --- | --- | --- | --- |
| username | Y | - | String | body | Unique username string |

| **Status Code** | **Description** |
| --- | --- |
| HTTP\_200\_OK | Username has been deleted. |
| HTTP\_400\_BAD\_REQUEST | Username not a string. |
| HTTP\_401\_UNAUTHORIZED | Authentication error. |
| HTTP\_404\_NOT\_FOUND | Username not found. |
| HTTP\_500\_INTERNAL\_SERVER\_ERROR | Something went wrong on the stepper\_backend app. |

**Example JSON POST:**
~~~~
{

 username : LeighPC,

 ip : 64.102.249.9

}
~~~~
**Example JSON data returned:**
~~~~
{

    error : Connect to #clus WiFi.,

    username : LeighPC,

    email : LeighPC@cmxtrackyoursteps.com,

    ip : 64.102.249.9

}
~~~~
**API-3: My Dashboard data**

**Description**

Once a user has successfully registered, you can then pull their &#39;My Dashboard data&#39; by simply using this API with their username. If successful JSON data will be returned with the required fields.

**URI**

/live/username\_data

**HTTP Method**

POST

**Content Type**

application/json

| **Name** | **Required** | **Default** | **Type** | **Location** | **Description** |
| --- | --- | --- | --- | --- | --- |
| username | Y | - | String | body | Unique username string |
| days | N | 5 | Integer | body | Number of historical days to return |

| **Status Code** | **Description** |
| --- | --- |
| HTTP\_200\_OK | Username found in database. |
| HTTP\_400\_BAD\_REQUEST | Username not a string. |
| HTTP\_401\_UNAUTHORIZED | Authentication error. |
| HTTP\_404\_NOT\_FOUND | Username not found in the database, no data returned. |
| HTTP\_500\_INTERNAL\_SERVER\_ERROR | Something went wrong on the stepper\_backend app. |

**Example JSON POST:**
~~~~
{

 username : Leigh,

 days: 5

}
~~~~
**Example JSON data returned:**
~~~~
[

    {

        distance\_day: [

            {

                date: 06/09/2018,

                km: 9.574,

                miles: 5.949

            },

            {

                date: 06/10/2018,

                km: 4.583,

                miles: 2.848

            },

            {

                date: 06/11/2018,

                km: 3.896,

                miles: 2.421

            }

        ],

        mac: 00:00:b4:92:4c:50,

        place: 16,

        total\_kilometres: 21.13,

        total\_miles: 13.129,

        username: Leigh

    }

]
~~~~
**API-3: Overall leader board**

**Description**

The overall leader board provides a summary for all users in the database. The JSON will return the distance covered in feet and metres. You can then convert this to steps by using an average step length of 2.5 feet per step.

**URI**

/live/leaderboard

**HTTP Method**

POST

**Content Type**

application/json

| **Name** | **Required** | **Default** | **Type** | **Location** | **Description** |
| --- | --- | --- | --- | --- | --- |
| number\_leaders | N | 5 | Integer | body | The number of leader board entries you would like returned. |

| **Status Code** | **Description** |
| --- | --- |
| HTTP\_200\_OK | Everything worked fine. |
| HTTP\_400\_BAD\_REQUEST | number\_leaders is \&gt; 100. |
| HTTP\_500\_INTERNAL\_SERVER\_ERROR | Something went wrong on the stepper\_backend app. |

**Example JSON POST:**
~~~~
{

 number_leaders : 5

}
~~~~
**Example JSON data returned:**
~~~~
{

    leaders: [

        {

            kilometres: 50.8,

            miles: 31.6,

            place: 1,

            username: skyking83

        },

        {

            kilometres: 37.6,

            miles: 23.3,

            place: 2,

            username: Bwernli

        },

        {

            kilometres: 36.1,

            miles: 22.4,

            place: 3,

            username: MeghanDonovan

        },

        {

            kilometres: 35.4,

            miles: 22,

            place: 4,

            username: jazzy

        },

        {

            kilometres: 34.1,

            miles: 21.2,

            place: 5,

            username: wilthias2

        }

    ],

    total\_kilometres: 10103,

    total\_miles: 6277.7

}
~~~~
**API-4: IP to username**

**Description**

Provide a method to return a username for an ip address if it has been previously registered. This is typically used to automate the login of the front-end web page.

**URI**

/live/ip\_username

**HTTP Method**

POST

**Content Type**

application/json

| **Name** | **Required** | **Default** | **Type** | **Location** | **Description** |
| --- | --- | --- | --- | --- | --- |
| ip | Y | NA | string | body | The ip address that is to be looked up. |

| **Status Code** | **Description** |
| --- | --- |
| HTTP\_200\_OK | Everything worked fine. |
| HTTP\_400\_BAD\_REQUEST | number\_leaders is \&gt; 100. |
| HTTP\_500\_INTERNAL\_SERVER\_ERROR | Something went wrong on the stepper\_backend app. |

**Example JSON POST:**
~~~~
{

 number_leaders : 5

}
~~~~
**Example JSON data returned:**
~~~~
{

    leaders: [

        {

            kilometres: 50.8,

            miles: 31.6,

            place: 1,

            username: skyking83

        },

        {

            kilometres: 37.6,

            miles: 23.3,

            place: 2,

            username: Bwernli

        },

        {

            kilometres: 36.1,

            miles: 22.4,

            place: 3,

            username: MeghanDonovan

        },

        {

            kilometres: 35.4,

            miles: 22,

            place: 4,

            username: jazzy

        },

        {

            kilometres: 34.1,

            miles: 21.2,

            place: 5,

            username: wilthias2

        }

    ],

    total\_kilometres: 10103,

    total\_miles: 6277.7

}
~~~~
## Database

The database schema consists of just 4 tables with very simple relationships. The most important requirement is to turn off logging to increase the performance of the database to ensure that the application can scale to tracking many clients.

### Database schema
~~~~
CREATE TABLE users (

        email varchar(100) NOT NULL PRIMARY KEY,

        salt varchar(255),

        hashed varchar(255),

        admin boolean,

        nickname varchar(255)

);

CREATE TABLE devices (

        mac macaddr NOT NULL PRIMARY KEY,

        owner varchar(100) REFERENCES users (email)

);

CREATE TABLE distance (

        mac macaddr PRIMARY KEY,

        mtrs real,

        floor\_id bigint,

        point\_1 point,

        point\_2 point,

        distance\_1to2 real,

        time timestamptz

    );

CREATE TABLE count (

        time timestamp PRIMARY KEY,

        user\_count integer DEFAULT 0,

        device\_count integer DEFAULT 0,

        notification\_count integer DEFAULT 0

);

CREATE TABLE distance\_history (

        time timestamptz NOT NULL,

        mac macaddr NOT NULL,

        mtrs real DEFAULT 0.0,

        PRIMARY KEY (time, mac)

);

ALTER TABLE count SET UNLOGGED;

ALTER TABLE distance SET UNLOGGED;

ALTER TABLE distance\_history SET UNLOGGED;

ALTER TABLE zone SET UNLOGGED;

CREATE ROLE cmx;

ALTER ROLE cmx LOGIN;

GRANT ALL ON count TO cmx;

GRANT ALL ON devices TO cmx;

GRANT ALL ON distance TO cmx;

GRANT ALL ON distance\_history TO cmx;

GRANT ALL ON users TO cmx;

GRANT ALL ON zone TO cmx;
~~~~

Typical table size for in the database is an event that managed 30,000 users:

users = 616Kbytes

devices = 232Kbyes

count = 8.8Mbytes

distance = 4.3Mbytes

distance\_history = 15Mbytes

## Database backup

A backup of the database only requires around 18Mbytes. A simple script can be used to create a backup:
~~~~

#!/bin/bash

logfile=/home/leigh/db\_backup/pgsql.log

backup\_dir=/home/leigh/db\_backup

touch $logfile

echo Starting backup of databases  \&gt;\&gt; $logfile

dateinfo=`date &#39;+%Y-%m-%d %H:%M:%S&#39;`

timeslot=`date &#39;+%Y%m%d%H%M&#39;`

/usr/bin/pg\_dump -U cmx cmx -f $backup\_dir/cmx-database-$timeslot.backup

echo Backup complete on $dateinfo for database: $i  \&gt;\&gt; $logfile

echo Done backup of databases $logfile
~~~~

## Server Installation

The system has been tested on Ubuntu 17.10 server, which can be downloaded from Ubuntu website:

[https://www.ubuntu.com/download/server](https://www.ubuntu.com/download/server)

### Hardware requirements

A server to support an event such as CLUS would require the following VM:

- RAM: 32GB
- DISK: 30GB
- CPU: 4 x vCPU

### Update server software

Get the latest list of packages and upgrade the server.

**COMMAND**
~~~~
sudo apt-get update

sudo apt-get upgrade
~~~~
### Configure static ip address

The server requires a static ip address to allow the frontend application to connect to.

**COMMAND**
~~~~

sudo vi /etc/netplan/01-netcfg.yaml

sudo netplan apply

Changes required to 01-netcfg.yaml

network:

 version: 2

 renderer: networkd

 ethernets:

   ens33:

     dhcp4: no

     dhcp6: no

     addresses: [192.168.1.2/24]

     gateway4: 192.168.1.1

     nameservers:

        search: [cisco.com]

       addresses: [8.8.8.8,8.8.4.4]
~~~~
### Software installation

The server will require the following software installed:

On the ubuntu server get the latest list of packages and upgrade everything:
~~~~

sudo apt-get update

sudo apt-get upgrade
~~~~

**Install Apache2 and dev files (needed to recompile mod\_wsgi if required)**
~~~~

sudo apt-get install apache2

sudo apt-get install apache2-dev
~~~~

**Ensure pip3 installed**
~~~~

sudo apt-get install python3-pip
~~~~

**Install virtualenv with pip3**
~~~~

sudo pip3 install virtualenv
~~~~

**Create virtual environement and activate**
~~~~

sudo mkdir /usr/local/venv/flask-app

python3 -m virtualenv /usr/local/venv/flask-app

source /usr/local/venv/flask-app/bin/activate
~~~~

**Create source directory and clone the source files from Git**
~~~~

mkdir /var/www/cmx-live

cd /var/www/cmx-live

git clone https://github.com/leigh-jewell/cmx-live
~~~~

**Load required python modules into virtual environment**
~~~~

pip install –r requirements.txt
~~~~

**Install postgresql software, create database and create schema**
~~~~

sudo apt-get install postgresql-9.6

sudo su – postgres

createdb cmx

psql databasename /var/www/cmx-live/create\_cmx\_db.sql
~~~~

**Download latest version of mod\_wsgi, configure for python3 and install**
~~~~

wget https://github.com/GrahamDumpleton/mod\_wsgi/archive/4.5.22.tar.gz -o mod\_wsgi\_4.5.22.tar.gz

tar xvfz mod\_wsgi-X.Y.tar.gz

./configure --with-python=/usr/bin/python3

make

make install
~~~~

**Tell Apache2 to load mod\_wsgi module**

Create a file in mods-available and add information to tell Apache where to find file

~~~~
mkdir /etc/apache2/mods-available

sudo vi mod\_wsgi.load
~~~~

**Add the following text into the file:**
~~~~
LoadModule wsgi\_module /usr/lib/apache2/modules/mod\_wsgi.so
~~~~

**Enable mod\_wsgi in Apache**
~~~~

sudo a2enmod mod\_wsgi
~~~~

**Create certificate for HTTPS on Apache**

Create self-signed certificate (or you can install a free certificate from https://letsencrypt.org/)
~~~~
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/ssl/private/apache-selfsigned.key -out /etc/ssl/certs/apache-selfsigned.crt
~~~~

**Create a strong Diffie-Hellman group**
~~~~
sudo openssl dhparam -out /etc/ssl/certs/dhparam.pem 2048
~~~~

**Create strong SSL configuration for Apache2**
~~~~
sudo vi /etc/apache2/conf-available/ssl-params.conf
~~~~
~~~~
SSLCipherSuite EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH

SSLProtocol All -SSLv2 -SSLv3

SSLHonorCipherOrder On

# Disable preloading HSTS for now.  You can use the commented out header line that includes

# the &quot;preload&quot; directive if you understand the implications.

#Header always set Strict-Transport-Security &quot;max-age=63072000; includeSubdomains; preload&quot;

Header always set Strict-Transport-Security &quot;max-age=63072000; includeSubdomains&quot;

Header always set X-Frame-Options DENY

Header always set X-Content-Type-Options nosniff

# Requires Apache \&gt;= 2.4

SSLCompression off

SSLSessionTickets Off

SSLUseStapling on

SSLStaplingCache &quot;shmcb:logs/stapling-cache(150000)

SSLOpenSSLConfCmd DHParameters &quot;/etc/ssl/certs/dhparam.pem
~~~~

**Enable the changes in Apache**
~~~~

sudo a2enmod ssl

sudo a2enmod headers

sudo a2ensite default-ssl

sudo a2enconf ssl-params
~~~~

**Check Apache configuration**
~~~~

sudo apache2ctl configtest

sudo systemctl restart apache2
~~~~

**Configure virtual host on Apache HTTP and HTTPS**
**HTTP connections**
~~~~
sudo vi /etc/apache2/000-default.conf

VirtualHost \*:80\

    ServerName live-cmx.cisco.com

    WSGIScriptAlias / **/var/www/cmx-live/cmx.wsgi**

    WSGIDaemonProcess **cmx\_http** group= **cmx\_http**

    WSGIPassAuthorization On

    \&lt;Directory **/var/www/cmx-live** \

       WSGIProcessGroup **cmx\_http**

       WSGIApplicationGroup %{GLOBAL}

        Order deny,allow

        Allow from all

    \&lt;/Directory\

/VirtualHost\

~~~~
**HTTPS Connections**
~~~~

\IfModule mod\_ssl.c\

        VirtualHost \_default\_:443\

                ServerName live-cmx

                DocumentRoot /var/www/html

                ErrorLog ${APACHE\_LOG\_DIR}/error.log

                CustomLog ${APACHE\_LOG\_DIR}/access.log combined

                SSLEngine on

                SSLCertificateFile      /etc/ssl/certs/apache-selfsigned.crt

                SSLCertificateKeyFile /etc/ssl/private/apache-selfsigned.key

                FilesMatch &quot;\.(cgi|shtml|phtml|php)$

                                SSLOptions +StdEnvVars

                /FilesMatch

                # WSGI Section for CMX

                #

                WSGIScriptAlias / /var/www/cmx-live/cmx.wsgi

                WSGIDaemonProcess cmx group=cmx\_http

                WSGIPassAuthorization On

                Directory /var/www/cmx-live

                        WSGIProcessGroup cmx

                        WSGIApplicationGroup %{GLOBAL}

                        Order deny,allow

                         Allow from all

               /Directory

                BrowserMatch bMSIE [2-6]\

                                nokeepalive ssl-unclean-shutdown \

                                downgrade-1.0 force-response-1.0

        /VirtualHost

/IfModule
~~~~
NOTE: For the option WSGIPassAuthorization On. This is needed for the HTTP basic authentication that is performed on the notifications from CMX.

**Ensure cmx.wsgi is the file used by Apache**

The git respository will contain a file called cmx.wsgi which Apache will open and run

This is in the virtual host configuration file WSGIScriptAlias / /var/www/cmx-live/cmx.wsgi which directs the WSGI module to open the cmx.wsgi file to run. This file contains

**Activate the virtual environment in /usr/local/venv/flask-app**

Activate the virtualenvironment that has been built
~~~~~
activate\_this = /usr/local/venv/flask-app/bin/activate\_this.py

with open(activate\_this) as file\_:

    exec(file\_.read(), dict(\_\_file\_\_=activate\_this))

# Now from the main cmx.py file load the Flask app

import sys

sys.path.insert(0, &quot;/var/www/cmx-live&quot;)

from cmx import app as application
~~~~~

**Group Permissions for mod\_wsgi**

To enable the cmx.py to log out to a file we need to implement some group permissions so that the mod\_wsgi process has permission to write to the /var/www/cmx-live directory

Create user
~~~~~
sudo useradd cmx\_http

Add to a new group

sudo usermod -G cmx\_http -a cmx\_http

sudo usermod -G cmx\_http -a www-data

/var/www/cmx-live

sudo chgrp -R cmx\_http \*
~~~~~

This group is configured in the Apache virtual host configuration file

# HTTP
~~~~~

sudo vi /etc/apache2/sites-available/000-default.conf

VirtualHost \*:80\

    ServerName live-cmx.cisco.com

    WSGIScriptAlias / /var/www/cmx-live/cmx.wsgi

    WSGIDaemonProcess **cmx\_http** group= **cmx\_http**

    WSGIPassAuthorization On

    \Directory /var/www/cmx-live\

       WSGIProcessGroup **cmx\_http**
~~~~~

**Get the latest updates from Git**

If the source has been updated since you cloned on Git, a you will need to update by pulling the latest version:
~~~~~
cd /var/www/cmx-live

git pull origin master

sudo service apache2 restart

tail /var/log/apache2/error.log
~~~~~

**CMX Configuration**

Create a notification on CMX to send a notification to the Ubuntu server running cmx.py

**Notification Settings**

This notification will fire a POST to the server configured on live-cmx.cisco.com (you change this to the ip of the server on site) at the URL /notification on port 80. It will fire when an associated client moves 50 feet. The HTTP header is an authorization token so that only valid notifications are accepted. The MAC address is hashed with the configured key.

These password need to be configured into config.ini with cmx.py on the host machine.

**Create username on CMX**

The stepper application needs to send an API request to the CMX to work out the mac address for the ip address that is provided. To allow this API to succeed a username and password needs to be created on the CMX. Browse to Manage  Users and created a user account and ensure this is the same as configured into config.ini on the stepper application.

## Configuration
**Config.ini**
In the /var/www/cmx-live directory on the Ubuntu server is a config.ini file, which controls how cmx.py behaves.

| LOGFILE | Directory where the cmx.py files are written. The mod\_wsgi daemon needs to have permission to write files here. |
| --- | --- |
| LOG\_LEVEL | Can be set to DEBUG for extensive debugging messages or INFO for just errors and informational messages. |
| APP\_SECRET\_KEY | Secret key that the Flask app uses to ensure sessions are kept secret. |
| NOTIFICATION\_USER | Username encoded into the notification token |
| NOTIFICATION\_PASSWORD | HTTP Basic Authentication password that is configured on the notification on the CMX. You need to convert this password into a token using something like Postman.   |
| API\_USER\_PASSWORD | Password used to get access to the API |
| HOST | IP address where the DB is located |
| DBNAME | Database name |
| DB\_USERNAME | Database username |
| DB\_PASSWORD | Database password |
| CMX\_USERNAME | Username used to query the CMX |
| CMX\_PASSWORD | Password used to query the CMX |
| CMX\_IP2MAC\_URL | URL to query the CMX |
| CMX\_HOST | List of CMX ip address to query, can include test to use for testing |
| CMX\_TIMEOUT | Timeout in seconds for query |
| CMX\_MOVEMENT\_DISTANCE | Distance configured on CMX for distance movement |
| CMX\_MAC\_HASH | CMX MAC hash password |
| MAX\_REGISTERED\_DEVICES | Maximum number of devices allowed per user |
