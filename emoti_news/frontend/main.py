import uvicorn

from emoti_news.frontend.frontend import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload_delay=5)
