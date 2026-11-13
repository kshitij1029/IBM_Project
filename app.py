"""Root launcher preserving existing local, test and Gunicorn commands."""
from backend.app import app, Config, create_app

if __name__ == "__main__":
    import os
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=Config.DEBUG,
    )
