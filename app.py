import os
from dotenv import load_dotenv

from app import create_app

load_dotenv()

app = create_app(os.getenv('FLASK_CONFIG', os.getenv('FLASK_ENV', 'default')).lower())


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=app.config.get('DEBUG', False)
    )
