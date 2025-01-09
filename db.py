import psycopg2
from datetime import datetime
import google.generativeai as genai

DATABASE_KEY = "<ссылка для подключения к базе данных>"


def get_db_connection():
    return psycopg2.connect(DATABASE_KEY)


def save_message(user_id, username):
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    request = '''
        INSERT INTO message_history (user_id, username, timestamp)
        VALUES (%s, %s, %s)
    '''
    cursor.execute(request, (user_id, username, timestamp))
    conn.commit()
    cursor.close()
    conn.close()


def verify_code(user_id, username, code):
    conn = get_db_connection()
    cursor = conn.cursor()
    request_check = "SELECT * FROM codes WHERE code = %s"
    cursor.execute(request_check, (code,))
    record = cursor.fetchone()

    if record:
        request_update = '''
            UPDATE codes
            SET user_id = %s, username = %s, updated_at = now() AT TIME ZONE 'Asia/Yekaterinburg'
            WHERE code = %s
        '''
        cursor.execute(request_update, (user_id, username, code))
        conn.commit()
        cursor.close()
        conn.close()
        return True, f"Код подтвержден. Добро пожаловать, {record[1]} {record[2]}!"
    else:
        cursor.close()
        conn.close()
        return False, "Код не найден. Проверьте правильность ввода."


def save_question_and_answer(user_id, question, answer=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    request = '''
        INSERT INTO test_results (user_id, question, answer, timestamp)
        VALUES (%s, %s, %s, %s)
    '''
    cursor.execute(request, (user_id, question, answer, timestamp))
    conn.commit()
    cursor.close()
    conn.close()


def save_analysis_result(user_id, username, evaluation):
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    request = '''
        INSERT INTO analysis_results (user_id, username, evaluation, timestamp)
        VALUES (%s, %s, %s, %s)
    '''
    cursor.execute(request, (user_id, username, evaluation, timestamp))
    conn.commit()
    cursor.close()
    conn.close()


def analyze_test_results(user_id, username):
    conn = get_db_connection()
    cursor = conn.cursor()

    request = "SELECT question, answer FROM test_results WHERE user_id = %s"
    cursor.execute(request, (user_id,))
    results = cursor.fetchall()

    if not results:
        return "Ошибка анализа: нет данных для анализа."

    results_text = "\n".join(
        [f"Вопрос: {row[0]}\nОтвет: {row[1]}\n" for row in results])
    prompt = f"Проанализируй ответы на тест и оцени, стоит ли брать человека на материально ответственную должность. Вот его ответы на вопросы:\n{
        results_text}"

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    evaluation = response.text.strip()

    save_analysis_result(user_id, username, evaluation)
    return evaluation
