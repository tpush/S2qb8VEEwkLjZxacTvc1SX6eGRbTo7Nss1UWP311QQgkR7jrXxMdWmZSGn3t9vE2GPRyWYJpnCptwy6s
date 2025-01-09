import telebot
import db
import questions

BOT_TOKEN = "<токен бота в Telegram>"
bot = telebot.TeleBot(BOT_TOKEN)
user_data = {}


@bot.message_handler(commands=['start'])
def start(message):
    bot_response = (
        "Здравствуйте! Вы запустили бот \"Надёжный сотрудник\".\n"
        "Для продолжения работы введите кодовое слово:"
    )
    db.save_message(message.from_user.id, message.from_user.username)
    bot.send_message(message.from_user.id, bot_response)
    bot.register_next_step_handler(message, handle_code_input)


def handle_code_input(message):
    user_id = message.from_user.id
    username = message.from_user.username
    code = message.text.strip()

    verified, bot_response = db.verify_code(user_id, username, code)
    bot.send_message(user_id, bot_response)

    if verified:
        user_data[user_id] = {'questions': [], 'current_question': 0}
        start_test(message)


def start_test(message):
    user_id = message.from_user.id
    if user_id not in user_data:
        bot.send_message(user_id, "Ошибка. Попробуйте снова начать тест.")

    user_data[user_id]['questions'] = questions.generate_questions()
    user_data[user_id]['current_question'] = 0
    ask_next_question(message)


def ask_next_question(message):
    user_id = message.from_user.id
    user_info = user_data.get(user_id)

    if not user_info or user_info['current_question'] >= len(user_info['questions']):
        bot.send_message(user_id, "Тест завершен! Спасибо за участие.")
        evaluation = db.analyze_test_results(user_id)
        bot.send_message(user_id, f"Оценка по результатам теста: {evaluation}")
        return

    question = user_info['questions'][user_info['current_question']]
    bot.send_message(user_id, f"Вопрос {user_info['current_question'] + 1}: {question}")
    user_info['current_question'] += 1


@bot.message_handler(content_types=['text'])
def handle_answers(message):
    user_id = message.from_user.id
    username = message.from_user.username

    if user_id in user_data:
        user_info = user_data[user_id]
        current_question_index = user_info['current_question'] - 1

        if current_question_index < 0:
            bot.send_message(user_id, "Начните тест с команды /start.")
            return

        question = user_info['questions'][current_question_index]
        answer = message.text
        db.save_question_and_answer(user_id, question, answer)

        if user_info['current_question'] < len(user_info['questions']):
            ask_next_question(message)
        else:
            bot.send_message(user_id, "Тест завершен! Спасибо за участие.")
            evaluation = db.analyze_test_results(user_id, username)
            bot.send_message(
                user_id, f"Оценка по результатам теста: {evaluation}")
    else:
        bot.send_message(user_id, "Начните тестирование с команды /start.")


bot.polling(none_stop=True)
