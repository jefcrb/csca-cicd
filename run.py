from app import create_app
from app.routes import init_routes
from dotenv import load_dotenv

load_dotenv('.env')
load_dotenv('secret.env')

app = create_app()
init_routes(app)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
