import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    EXPLAIN_TEMPLATE_LOADING = True
