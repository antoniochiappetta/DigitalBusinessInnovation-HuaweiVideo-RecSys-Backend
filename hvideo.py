from app import app, db
from app.models import User, Movie, Interaction


# Create shell context for debugging with `flask shell`
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Movie': Movie, 'Interaction': Interaction}
