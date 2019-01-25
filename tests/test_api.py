from base64 import b64encode
import json
import pytest
import cmx
from measurement.measures import Distance
from time import sleep

@pytest.fixture
def client():
    cmx.app.config['TESTING'] = True
    client = cmx.app.test_client()
#    valid_credentials = b64encode(
#        b'cmx:ugBxWwaI1/gjkFaLqLs9dMGvZLGsgthOyJOFHlwhChez2pQJkm+V95DK7U7dYjcWS/cs3hm5wn4XSmLaE14r8WWVWHSAcYkUuvX').decode(
#        'utf-8')
    user = cmx.app.config['NOTIFICATION_USER']
    password = cmx.app.config['NOTIFICATION_PASSWORD']
    user_pass = user + ':' + password
    cmx.app.config['valid_credentials'] = b64encode(str.encode(user_pass)).decode('utf-8')
    cmx.app.config['test_username'] = 'test_register_username6'
    cmx.app.config['test_username2'] = 'test_register_username7'
    cmx.app.config['test_ip'] = '10.16.0.110'
    cmx.app.config['test_ip2'] = '10.16.0.111'

    yield client


def test_webpage(client):
    """Test the web page is up"""

    rv = client.get('/')
    assert b'Sweat for Swag' in rv.data


def test_register_username(client):
    """API: register a username"""

    json_data = json.dumps({'username': cmx.app.config['test_username'], 'ip': cmx.app.config['test_ip']})
    client_response = client.post('/live/register_username', headers={'Authorization': 'Basic ' + cmx.app.config['valid_credentials']},
                           data =json_data, content_type='application/json')
    response_dict = json.loads(client_response.data.decode('utf-8'))
    print(response_dict)
    if 'mac' in response_dict:
        cmx.app.config['test_mac'] = response_dict['hash_mac']

    assert client_response.status_code == 201
    assert response_dict['username'] == cmx.app.config['test_username']
    assert response_dict['db_result'] == 1

def test_register_same_entry(client):
    """API: register a username with same ip"""

    json_data = json.dumps({'username': cmx.app.config['test_username'], 'ip': cmx.app.config['test_ip']})
    client_response = client.post('/live/register_username', headers={'Authorization': 'Basic ' + cmx.app.config['valid_credentials']},
                           data =json_data, content_type='application/json')
    response_dict = json.loads(client_response.data.decode('utf-8'))
    print(response_dict)

    assert client_response.status_code == 200
    assert response_dict['username'] == cmx.app.config['test_username']
    assert response_dict['info'] == 'Username already registered with that mac, nothing to do'

def test_register_duplicate_username(client):
    """API: register a duplicate username with same different ip"""

    json_data = json.dumps({'username': cmx.app.config['test_username'], 'ip': cmx.app.config['test_ip2']})
    client_response = client.post('/live/register_username', headers={'Authorization': 'Basic ' + cmx.app.config['valid_credentials']},
                           data =json_data, content_type='application/json')
    response_dict = json.loads(client_response.data.decode('utf-8'))
    print(response_dict)

    assert client_response.status_code == 409
    assert response_dict['username'] == cmx.app.config['test_username']
    assert response_dict['error'] == 'Username already registered'


def test_register_duplicate_device(client):
    """API: register a username"""

    json_data = json.dumps({'username': cmx.app.config['test_username2'], 'ip': cmx.app.config['test_ip']})
    client_response = client.post('/live/register_username', headers={'Authorization': 'Basic ' + cmx.app.config['valid_credentials']},
                           data =json_data, content_type='application/json')
    response_dict = json.loads(client_response.data.decode('utf-8'))
    print(response_dict)

    assert client_response.status_code == 409
    assert response_dict['error'] == 'Device already registered with another username {}.'.format(cmx.app.config['test_username'])


def test_notification_device(client):
    """API: send 10 test CMX notifications for a straight line"""
    max_move_ft = Distance(m=cmx.app.config['MAX_MTRS_SEC']).ft
    x = 0
    for i in range(10):
        x += max_move_ft
        json_data = json.dumps({'notifications': [{'moveDistanceInFt' : max_move_ft,
                                                   'deviceId' : cmx.app.config['test_mac'],
                                                   'locationCoordinate' : {'x':x, 'y':200+i},
                                                   'floorId' : 999
                                                   }
                                                  ]
                                }
                               )
        client_response = client.post('/notification', headers={'Authorization': 'Basic ' + cmx.app.config['valid_credentials']},
                               data =json_data, content_type='application/json')
        sleep(1)

    assert client_response.status_code == 200


def test_userame_data(client):
    """API: get data for a particular username"""

    json_data = json.dumps({'username': cmx.app.config['test_username'], 'days': 5})
    client_response = client.post('/live/username_data',
                                  headers={'Authorization': 'Basic ' + cmx.app.config['valid_credentials']},
                                  data=json_data, content_type='application/json')
    response_dict = json.loads(client_response.data.decode('utf-8'))
    print(response_dict)

    assert client_response.status_code == 200
    assert 'distance_day' in response_dict[0]
    assert 'date' in response_dict[0]['distance_day'][0]
    assert 'km' in response_dict[0]['distance_day'][0]
    assert response_dict[0]['distance_day'][0]['km'] > 0.0
    assert 'miles' in response_dict[0]['distance_day'][0]
    assert response_dict[0]['distance_day'][0]['miles'] > 0.0
    assert 'mac' in response_dict[0]
    assert 'place' in response_dict[0]
    assert 'total_kilometres' in response_dict[0]
    assert response_dict[0]['total_kilometres'] > 0.0
    assert 'total_miles' in response_dict[0]
    assert response_dict[0]['total_miles'] > 0.0
    assert response_dict[0]['username'] == cmx.app.config['test_username']

def test_notification_device_too_fast(client):
    """API: send 10 test CMX notifications for a straight line, but too fast"""
    max_move_ft = Distance(m=cmx.app.config['MAX_MTRS_SEC']).ft * 2
    x = 0
    for i in range(10):
        x += max_move_ft
        json_data = json.dumps({'notifications': [{'moveDistanceInFt' : max_move_ft,
                                                   'deviceId' : cmx.app.config['test_mac'],
                                                   'locationCoordinate' : {'x':x, 'y':200+i},
                                                   'floorId' : 999
                                                   }
                                                  ]
                                }
                               )
        client_response = client.post('/notification', headers={'Authorization': 'Basic ' + cmx.app.config['valid_credentials']},
                               data =json_data, content_type='application/json')
        sleep(1)

    assert client_response.status_code == 200


def test_leaderboard(client):
    """API: get the leaderboard"""

    json_data = json.dumps({'number_leaders': 1})
    client_response = client.post('/live/leaderboard',
                                  headers={'Authorization': 'Basic ' + cmx.app.config['valid_credentials']},
                                  data=json_data, content_type='application/json')
    response_dict = json.loads(client_response.data.decode('utf-8'))
    print(response_dict)

    assert client_response.status_code == 200
    assert len(response_dict['leaders']) >= 1
    assert 'kilometres' in response_dict['leaders'][0]
    assert 'miles' in response_dict['leaders'][0]
    assert 'place' in response_dict['leaders'][0]
    assert 'username' in response_dict['leaders'][0]
    assert response_dict['leaders'][0]['kilometres'] >= 0.0
    assert response_dict['leaders'][0]['miles'] >= 0.0
    assert response_dict['leaders'][0]['miles'] >= 1
    assert 'leaders' in response_dict
    assert 'total_kilometres' in response_dict
    assert 'total_miles' in response_dict
    assert response_dict['total_kilometres'] >= 0.0
    assert response_dict['total_miles'] >= 0.0


def test_delete_username(client):
    """API: delete a valid username"""

    json_data = json.dumps({'username': cmx.app.config['test_username']})
    client_response = client.post('/live/delete_username', headers={'Authorization': 'Basic ' + cmx.app.config['valid_credentials']},
                           data =json_data, content_type='application/json')
    response_dict = json.loads(client_response.data.decode('utf-8'))
    print(response_dict)

    assert client_response.status_code == 200
    assert response_dict['username'] == cmx.app.config['test_username']



def test_delete_username_not_exist(client):
    """API: test delete non existant username"""

    json_data = json.dumps({'username': cmx.app.config['test_username']})
    client_response = client.post('/live/delete_username', headers={'Authorization': 'Basic ' + cmx.app.config['valid_credentials']},
                           data =json_data, content_type='application/json')
    response_dict = json.loads(client_response.data.decode('utf-8'))
    print(response_dict)

    assert client_response.status_code == 404


