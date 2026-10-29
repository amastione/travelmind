from openai import OpenAI

API_KEY = "AQ.Ab8RN6JTeyT8x0cUSjBOZj9znAdcPg4rC-Knq2Rc2iNSDfbpBw"

client = OpenAI(
    api_key=API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

try:
    response = client.chat.completions.create(
        model="gemini-3-flash-preview",
        messages=[
            {
                "role": "user",
                "content": "Ответь только одним словом: OK",
            }
        ],
        max_tokens=10,
    )

    print("✅ Gemini API работает.")
    print("Ответ:", response.choices[0].message.content)

except Exception as error:
    print("❌ Gemini API вернул ошибку:")
    print(type(error).__name__)
    print(str(error))
