import os

from flask import Flask, request
import logging
import json
import random

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

cities = {
    'москва': ['1540737/daa6e420d33102bf6947',
               '213044/7df73ae4cc715175059e'],
    'нью-йорк': ['1652229/728d5c86707054d4745f',
                 '1030494/aca7ed7acefde2606bdc'],
    'париж': ["1652229/f77136c2364eb90a3ea8",
              '3450494/aca7ed7acefde22341bdc']
}

sessionStorage = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info(f'Request: {request.json!r}')
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info(f'Response: {response!r}')
    return json.dumps(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']
    if req['session']['new']:
        res['response']['text'] = 'Привет! Назови свое имя!'
        sessionStorage[user_id] = {
            'first_name': None
        }
        return

    if sessionStorage[user_id]['first_name'] is None:
        first_name = get_first_name(req)
        if first_name is None:
            res['response']['text'] = \
                'Не расслышала имя. Повтори, пожалуйста!'
        else:
            sessionStorage[user_id]['first_name'] = first_name
            sessionStorage[user_id]["guessed_cities"] = []
            sessionStorage[user_id]['game_started'] = False
            res['response'][
                'text'] = 'Приятно познакомиться, ' \
                          + first_name.title() \
                          + '. Я - Алиса. Отгадаешь город по фото?'
            res['response']['buttons'] = [
                {
                    'title': 'Да',
                    'hide': True
                },
                {
                    'title': 'Нет',
                    'hide': True
                },
                {
                    'title': 'Помощь',
                    'hide': True
                }
            ]
    else:
        if not sessionStorage[user_id]["game_started"]:
            if 'да' in req['request']['nlu']['tokens']:
                if len(sessionStorage[user_id]['guessed_cities']) == 3:
                    res['response']['text'] = "Ты отгадал все города!"
                    res['end_session'] = True
                else:
                    sessionStorage[user_id]["game_started"] = True
                    sessionStorage[user_id]['attempt'] = 1
                    game_play(res, req)
            elif 'нет' in req['request']['nlu']['tokens']:
                res['response']['text'] = "Ну и ладно!"
                res['end_session'] = True
            else:
                res['response']['text'] = "Ваш ответ непонятен! Да или нет?"
                res['response']['buttons'] = [
                    {
                        'title': 'Да',
                        'hide': True
                    },
                    {
                        'title': 'Нет',
                        'hide': True
                    },
                    {
                        'title': 'Помощь',
                        'hide': True
                    }
                ]
        else:
            game_play(res, req)


def game_play(res, req):
    user_id = req['session']['user_id']
    attempt = sessionStorage[user_id]['attempt']
    if attempt == 1:
        city = random.choice(list(cities))
        while city in sessionStorage[user_id]['guessed_cities']:
            city = random.choice(list(cities))
        sessionStorage[user_id]["city"] = city
        res['response']['card'] = {
            "type": "BigImage",
            "title": "Что это за город?",
            "image_id": cities[city][attempt - 1],
        }
        res["response"]['text'] = "Тогда сыграем!"
        res['response']['buttons'] = [
            {
                'title': 'Помощь',
                'hide': True
            }
        ]
    else:
        city = sessionStorage[user_id]['city']
        if get_city(req) == city:
            res['response']['text'] = "Правильно! Сыграем еще раз?"
            sessionStorage[user_id]["guessed_cities"].append(city)
            sessionStorage[user_id]["game_started"] = False
            res['response']['buttons'] = [
                {
                    'title': 'Да',
                    'hide': True
                },
                {
                    'title': 'Нет',
                    'hide': True
                },
                {
                    'title': 'Помощь',
                    'hide': True
                }
            ]
        else:
            if attempt == 2:
                res['response']['card'] = {
                    "type": "BigImage",
                    "title": "Неправильно! Вот тебе еще одна картинка!",
                    "image_id": cities[city][attempt - 1],
                }
                res["response"]['text'] = "А вот и не угадал!"
            else:
                res["response"]['text'] = f"Ты пытался! Это город {city}. Сыграем еще раз?"
                sessionStorage[user_id]["game_started"] = False
                sessionStorage[user_id]["guessed_cities"].append(city)
    sessionStorage[user_id]['attempt'] += 1


def get_city(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.GEO':
            return entity['value'].get('city', None)


def get_first_name(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.FIO':
            return entity['value'].get('first_name', None)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)