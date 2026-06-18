from flask import Flask, render_template, request, jsonify
import os
import json
import re

app = Flask(__name__)

EXCUSES = {
    "late": [
        {"text": "У меня с утра не завелась машина — аккумулятор сдох прямо во дворе. Пришлось искать прикуриватель у соседей, а потом стоять в пробке из-за аварии на Садовом.", },
        {"text": "Мне ночью написал клиент с горящим вопросом, я отвечал до 3 ночи. Утром просто не услышал будильник.", },
        {"text": "В нашем районе с утра отключили свет — не мог ни такси вызвать, ни расписание посмотреть.", },
    ],
    "homework": [
        {"text": "Я начал делать задание, но в условии есть неточность — потратил два часа пытаясь разобраться. Решил переспросить.", },
        {"text": "У меня вчера резко заболел младший брат — 39 температура, родители на работе. Весь вечер с ним просидел.", },
        {"text": "Я сделал, но файл не сохранился — комп завис и всё слетело. Начал заново но не успел.", },
    ],
    "birthday": [
        {"text": "Я помнил! Просто решил поздравить чуть позже — когда все забудут, ты получишь неожиданный привет.", },
        {"text": "У меня телефон слетел и все напоминания сбросились. Три человека в этом месяце именинники, всех пропустил.", },
        {"text": "Я специально ждал чтобы поздравить лично и вдумчиво. Массовые поздравления — это шаблон.", },
    ],
    "message": [
        {"text": "Я увидел сообщение в неудобный момент, хотел ответить нормально а не второпях — и забыл вернуться.", },
        {"text": "Телефон лежал на беззвучном весь день — было важное мероприятие. Увидел только сейчас.", },
        {"text": "У меня в мессенджере глюк — сообщение показало как прочитанное но уведомление не пришло.", },
    ],
    "meeting": [
        {"text": "У меня в календаре встреча стояла на час позже — видимо invite обновили только у себя. Я ждал, думал встреча отменилась.", },
        {"text": "Был в зоне без связи — ездил в область. Вернулся — увидел пропущенные. Готов провести встречу сегодня.", },
        {"text": "Параллельно была критическая ситуация с другим проектом — нужно было срочно принять решение. Давай перенесём.", },
    ],
    "report": [
        {"text": "Я хотел сдать качественный отчёт — нашёл расхождения в данных и начал перепроверять. Лучше задержать чем сдать с ошибками.", },
        {"text": "Мне не хватало данных от смежного отдела — запрашивал три раза. Как только получу — сразу закрою.", },
        {"text": "Сервер лёг в самый ответственный момент — я уже почти закончил. Как только поднимут — отправлю.", },
    ],
}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/excuse/preset", methods=["POST"])
def get_preset_excuse():
    data = request.json
    situation = data.get("situation")
    current_index = data.get("index", 0)

    if situation not in EXCUSES:
        return jsonify({"error": "Ситуация не найдена"}), 400

    excuses = EXCUSES[situation]
    next_index = (current_index + 1) % len(excuses)
    excuse = excuses[next_index]

    return jsonify({
        "text": excuse["text"],
        "index": next_index,
        "mode": "preset"
    })


@app.route("/api/excuse/ai", methods=["POST"])
def get_ai_excuse():
    data = request.json
    situation_text = data.get("situation_text", "")

    if not situation_text:
        return jsonify({"error": "Опишите ситуацию"}), 400

    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)

            message = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=600,
                messages=[{
                    "role": "user",
                    "content": f"""Ты эксперт по убедительным отмазкам. Твоя задача:
1. Придумай максимально убедительную и реалистичную отмазку для ситуации
2. Оцени её правдоподобность от 1 до 10
3. Дай короткое объяснение оценки (1 предложение)

Ситуация: {situation_text}

Ответь СТРОГО в формате JSON без markdown:
{{"text": "текст отмазки", "rating": 8.5, "reason": "объяснение оценки"}}"""
                }]
            )

            response_text = message.content[0].text.strip()
            # Убираем markdown если есть
            response_text = re.sub(r'```json\s*|\s*```', '', response_text).strip()
            result = json.loads(response_text)

            return jsonify({
                "text": result.get("text", ""),
                "rating": float(result.get("rating", 7.0)),
                "reason": result.get("reason", ""),
                "mode": "ai"
            })

        except Exception as e:
            # Fallback если API не сработал
            return jsonify({
                "text": "Ситуация вышла из-под контроля по независящим от меня причинам. Готов объяснить всё лично при встрече.",
                "rating": 6.5,
                "reason": f"AI временно недоступен: {str(e)[:50]}",
                "mode": "fallback"
            })
    else:
        # Заглушка без API ключа
        return jsonify({
            "text": "Понимаю что это звучит неправдоподобно, но именно так всё и произошло. У меня есть подтверждение если нужно.",
            "rating": 7.2,
            "reason": "Для реального AI анализа добавьте ANTHROPIC_API_KEY в переменные окружения",
            "mode": "stub"
        })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
