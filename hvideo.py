from app import app
from app.models import User, Movie


# Create shell context for debugging with `flask shell`
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Movie': Movie}
