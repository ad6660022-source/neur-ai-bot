from aiogram.fsm.state import State, StatesGroup


class ChatGPTState(StatesGroup):
    chatting = State()


class ClaudeState(StatesGroup):
    chatting = State()


class DeepSeekState(StatesGroup):
    chatting = State()


class SaveChatState(StatesGroup):
    waiting_name = State()


class AdminGrantState(StatesGroup):
    waiting_user_id = State()
    waiting_plan = State()


class AdminBanState(StatesGroup):
    waiting_user_id = State()


class AdminBroadcastState(StatesGroup):
    waiting_message = State()


class ImageState(StatesGroup):
    waiting_prompt = State()
