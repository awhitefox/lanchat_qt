from .return_codes import *

ERROR_STRINGS = {
    UNKNOWN_ERROR: "Неизвестная ошибка",
    BAD_PAYLOAD: "Неправильная струткура пакета",
    NOT_AUTHORIZED: "Требуется авторизация",
    USER_EXISTS: "Пользователь с таким именем уже есть на сервере",
    BAD_USERNAME: "Имя пользователя слишком длинное или не содержит символов",
}
