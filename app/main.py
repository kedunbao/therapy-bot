from fastapi import FastAPI
from pydantic import BaseModel
import requests
from app.questions import QUESTIONS

app = FastAPI()


class ChatRequest(BaseModel):
    message: str


@app.get("/")
def read_root():
    return {"message": "服务启动成功！"}


@app.post("/chat")
def chat(request: ChatRequest):
    user_text = request.message

    # 1. 先生成安慰回复
    prompt = f"""
你是一个温和、克制、共情的中文心理陪伴助手。
请根据用户输入，给出简短、自然、像微信聊天一样的回复。

要求：
1. 先共情，再轻微引导；
2. 不要说教；
3. 不要长篇大论；
4. 不要做医学诊断；
5. 回复控制在 2 到 4 句话。

用户输入：
{user_text}
"""

    reply_response = requests.post(
        "http://127.0.0.1:11434/api/generate",
        json={
            "model": "qwen:7b",
            "prompt": prompt,
            "stream": False
        },
        timeout=120
    )

    reply_result = reply_response.json()
    reply = reply_result["response"].strip()

    # 2. 再逐题评分
    scores = {}

    for key, question in QUESTIONS:
        score_prompt = f"""
请根据以下用户对话，对该问题打分（0-3分）：

用户对话：
{user_text}

问题：
{question}

评分标准：
0 = 没有表现
1 = 轻微
2 = 中等
3 = 严重

只返回一个数字（0-3），不要解释。
"""

        score_response = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={
                "model": "qwen:7b",
                "prompt": score_prompt,
                "stream": False
            },
            timeout=120
        )

        score_result = score_response.json()
        score_text = score_result["response"].strip()
        scores[key] = score_text

    # 3. 返回回复和评分
    return {
        "reply": reply,
        "scores": scores
    }