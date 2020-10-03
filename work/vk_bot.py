import json
import os
import re
import requests
import threading
import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType

from work.GameLife import GameLife


class VkBot:

    def __init__(self, _token):
        # API-ключ созданный ранее
        self.token = _token

        # Авторизуемся как сообщество
        self.vk_session = vk_api.VkApi(token=_token)

        # Работа с сообщениями
        self.longpoll = VkLongPoll(self.vk_session)
        self.vk = self.vk_session.get_api()

        self.mood = "main"
        self.keyboard = None

        self._set_standard_keyboard()

        self.game = GameLife()

        self.name_gif = 0

        self.generation_options = ["Глайдер", "Случайное распределение",
                                   "Гауссово распределение"]

    def _get_new_message(self, user_id, text_message):
        name_gif = str(self.name_gif) + ".gif"

        if self.mood == "main":
            if text_message in self.generation_options:
                self._write_message(user_id,
                                    "Через 20 секунд я пришлю вам сгенерированную гифку :)")
                if text_message == "Глайдер":
                    self.game.play_glider(name_gif)
                elif text_message == "Случайное распределение":
                    self.game.play_random_distribution(name_gif)
                elif text_message == "Гауссово распределение":
                    self.game.play_gauss_distribution(name_gif)
                self._send_gif(user_id, name_gif, text_message)
            elif text_message == "Изменить размер поля":
                self.mood = "change_size"
                self._set_change_size_keyboard()
                self._write_message(user_id, "Введи 2 числа от 5 до 40, \n"
                                             "Или выбери нужную кнопку:")
            else:
                self._write_message(user_id, "Я не понял, что вы хотите\n"
                                             "Нажмите на нужную кнопку")

                # обработка кнопок в настроках
        elif self.mood == "change_size":
            value = []
            if self._is_list_number(text_message, value):
                self.game.x = value[0]
                self.game.y = value[1]

                self.mood = "main"
                self._set_standard_keyboard()
                self._write_message(user_id, "Вы ввели новые размеры!")
                self._write_message(user_id, "Ткни нужную кнопку!")
            elif text_message == "Вернуться":
                self.mood = "main"
                self._set_standard_keyboard()
                self._write_message(user_id, "Ткни нужную кнопку!")
            else:
                self._write_message(user_id, "Неправильный ввод! \n"
                                             "Введи 2 числа от 5 до 40 через пробел\n"
                                             "Или выбери нужную кнопку:")

    # проверяет, состоит ли text_message из двух чисел,
    # если состоит, то в value запишем эти 2 числа
    def _is_list_number(self, text_message, value):
        result = re.match(r'^[ ]*[\d]+[ ]+[\d]+[ ]*$', text_message)
        if result is not None:
            res_list = result.group(0).split()
            value.append(int(res_list[0]))
            value.append((int(res_list[1])))
            return True
        else:
            return False

    # вывести message от user_id в консоль
    def _print_new_message(self, user_id, message):
        print("Пришло новое сообщение от ", "https://vk.com/id", user_id,
              ", в котором написано - ", message,
              "\n", sep="", end="")

    # отправим user_id гифку
    def _send_gif(self, user_id, name_gif, message_to_client=""):
        upload_url = \
        self.vk.docs.getMessagesUploadServer(type='doc', peer_id=user_id)[
            'upload_url']
        response = requests.post(upload_url,
                                 files={"file": open(name_gif, "rb")})
        result = json.loads(response.text)
        new_json = self.vk.docs.save(file=result['file'])

        self.vk.messages.send(user_id=user_id, message=message_to_client,
                              attachment='doc%s_%s' % (
                              new_json["doc"]['owner_id'],
                              new_json["doc"]['id']),
                              random_id=0)
        os.remove(name_gif)

    # клавиатура для изменения размера
    def _set_change_size_keyboard(self):
        self.keyboard = VkKeyboard(one_time=False)

        self.keyboard.add_button("10 10", color=VkKeyboardColor.POSITIVE)
        self.keyboard.add_button("20 20", color=VkKeyboardColor.POSITIVE)
        self.keyboard.add_button("30 30", color=VkKeyboardColor.POSITIVE)
        self.keyboard.add_button("40 40", color=VkKeyboardColor.POSITIVE)

        self.keyboard.add_line()
        self.keyboard.add_button("Вернуться", color=VkKeyboardColor.PRIMARY)

    # клавиатура для для отправки нужной гифки
    def _set_standard_keyboard(self):
        self.keyboard = VkKeyboard(one_time=False)
        self.keyboard.add_button("Глайдер", color=VkKeyboardColor.POSITIVE)
        self.keyboard.add_button("Случайное распределение",
                                 color=VkKeyboardColor.POSITIVE)
        self.keyboard.add_button("Гауссово распределение",
                                 color=VkKeyboardColor.POSITIVE)

        self.keyboard.add_line()
        self.keyboard.add_button("Изменить размер поля",
                                 color=VkKeyboardColor.PRIMARY)

    # отправка сообщения message пользователю user_id
    def _write_message(self, user_id, message):
        self.vk.messages.send(user_id=user_id, message=message, random_id=0,
                              keyboard=self.keyboard.get_keyboard())

    def main(self):
        # Основной цикл
        for event in self.longpoll.listen():

            # Если пришло новое сообщение
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.from_user:
                # для каждой гифки будет свой номер
                self.name_gif += 1
                # в отдельном потоке запустим обработку сообщения, чтобы бот не "зависал" на время генерации гифки
                thread = threading.Thread(target=self._get_new_message,
                                          args=(event.user_id, event.text))
                thread.start()


def new_main():
    token = "your_token"
    bot = VkBot(token)
    bot.main()


new_main()
