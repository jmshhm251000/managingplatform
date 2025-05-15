import logging, datetime, re
from concurrent.futures import ThreadPoolExecutor
from flask import Blueprint, current_app, request
from flask import copy_current_request_context
from ..mongodb import mongo
from ..utils import login_required
from llama_index.llms.ollama import Ollama
from llama_index.core.llms import ChatMessage


# Set up a logger for this module using a plain text formatter
logger = logging.getLogger(__name__)
# Create a Blueprint for your webhook
webhook_bp = Blueprint('webhook', __name__)

classifier_llm = Ollama(model="llama3.2", request_timeout=60.0)
executor = ThreadPoolExecutor(max_workers=10)


@webhook_bp.route('/webhook', methods=['GET', 'POST'])
def webhook():
    VERIFY_TOKEN = current_app.config.get('VERIFY_TOKEN')

    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        # Log the GET request using a formatted string
        logger.info(
            "GET webhook verification request",
            extra={
                "mode": mode,
                "token": token,
                "challenge": challenge,
                "remote_addr": request.remote_addr,
                "url": request.url,
                "field": request.args.get('field'),

            }
        )
        
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            logger.info("Webhook verified successfully")
            return challenge, 200
        else:
            logger.warning(
                "Verification token mismatch",
                extra={
                    "mode": mode,
                    "token": token,
                    "remote_addr": request.remote_addr
                }
            )
            return 'Verification token mismatch', 403

    elif request.method == 'POST':
        data = request.get_json()
        # Log POST request details using string formatting
        logger.info(
            "POST webhook event received",
            extra={
                "method": request.method,
                "url": request.url,
                "remote_addr": request.remote_addr,
                "headers": dict(request.headers),
                "data": data
            }
        )

        if data.get("object") != "instagram":
            return "IGNORED", 200

        try:
            for entry in data.get("entry", []):
                # 1) Newer "messaging" style
                for msg in entry.get("messaging", []):
                    store_dm(msg)

                # 2) Older "changes / field == messages" style
                for change in entry.get("changes", []):
                    if change.get("field") == "messages":
                        store_dm(change["value"])


        except Exception:
            logger.exception("Error parsing / storing webhook event")

        return 'EVENT_RECEIVED', 200


@webhook_bp.route('/executor_status', methods=['GET'])
@login_required
def executor_status():
    """Current ThreadPoolExecutor Stats"""
    try:
        active_tasks = executor._work_queue.qsize()
        max_workers = executor._max_workers
        running_workers = max_workers - active_tasks

        return {
            "max_workers": max_workers,
            "running_workers_estimate": running_workers,
            "pending_queue_size": active_tasks
        }, 200
    except Exception as e:
        return {"error": str(e)}, 500


def store_dm(msg):
    message_id   = msg.get("message", {}).get("mid")
    sender_id    = msg.get("sender", {}).get("id")
    recipient_id = msg.get("recipient", {}).get("id")
    text         = msg.get("message", {}).get("text", "")
    ts_ms        = int(msg.get("timestamp", 0))
    ts_sec       = ts_ms / 1000 if ts_ms > 1e12 else ts_ms
    ts_dt        = datetime.datetime.utcfromtimestamp(ts_sec)

    doc = {
        "message_id":   message_id,
        "sender_id":    sender_id,
        "recipient_id": recipient_id,
        "text":         text,
        "timestamp":    ts_dt,
        "platform":     "instagram",
        "raw":          msg
    }

    try:
        mongo.db.instagram_dm.insert_one(doc)
        logger.info("DM stored", extra={"mid": message_id})
        trigger_llm_background(doc)
    except mongo.cx.errors.DuplicateKeyError:
        logger.info("Duplicate mid skipped", extra={"mid": message_id})


def trigger_llm_background(doc):
    @copy_current_request_context
    def wrapped():
        process_llm_task(doc)

    executor.submit(wrapped)


def process_llm_task(doc):
    try:
        category = categorize_with_llm(doc["text"])
    except Exception as e:
        logger.error(f"[LLM Error - Categorization] {e}")
        category = "미분류"

    try:
        response = generate_response_with_llm(doc["text"])
    except Exception as e:
        logger.error(f"[LLM Error - Response Generation] {e}")
        response = "죄송합니다. 현재 요청을 처리할 수 없습니다."

    try:
        mongo.db.instagram_dm.update_one(
            {"message_id": doc["message_id"]},
            {"$set": {"category": category, "response": response}}
        )
    except Exception as e:
        logger.error(f"[MongoDB Update Error] {e}")


def categorize_with_llm(text: str) -> str:
    prompt = f"""
다음 메시지를 아래 카테고리 중 하나로만 분류해줘:
기기/출력/결제 문제, 분실물, 협업 제안 / B2B,
웨딩 대여 문의, 지역 외 문의, 가격 문의,
소품 착오/반납, 바우처 오류/만료, 접근성 문의,
디지털 재출력 문의, 예약 관련 문의, QR 링크/클라우드 오류 문의

메시지: "{text}"
"""

    messages = [
        ChatMessage(
            role="system", content="you are to categorize the user's query"
        ),
        ChatMessage(role="user", content=prompt),
    ]
    resp = classifier_llm.chat(messages)
    text = str(resp).strip()
    processed_text = re.sub(r"(?i)^assistant:\s*", "", text).strip()

    return processed_text


def generate_response_with_llm(text: str) -> str:
    chatbot = getattr(current_app, "chatbot", None)
    if chatbot is None:
        raise ValueError("Chatbot is not initialized")
    
    return chatbot._query(text).strip()
