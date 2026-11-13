"""Repository-root launcher retained for local and Gunicorn compatibility."""
from backend.app import app, Config

if __name__ == "__main__":
    import os
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=Config.DEBUG,
    )
