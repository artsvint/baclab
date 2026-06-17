import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    APP_NAME = "ЛИС «Картотека»"
    PATIENTS_PAGE_LIMIT = 100
    TESTS_PAGE_LIMIT = 200
