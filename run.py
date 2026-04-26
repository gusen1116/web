import sys
import os

# Add the current directory to sys.path so that the ``app`` package is importable
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Development environment defaults
if not os.environ.get('SECRET_KEY'):
    os.environ['SECRET_KEY'] = 'dev-only-secret-key-do-not-use-in-production'
    os.environ.setdefault('FLASK_ENV', 'development')
    os.environ.setdefault('CACHE_TYPE', 'simple')

# Print diagnostic information to help debug path issues
print("======== sys.path ========")
for p in sys.path:
    print(p)
print("==========================")
print(f"Current working directory: {os.getcwd()}")
print(f"Script directory: {current_dir}")

# Ensure the ``app`` package exists before attempting to import it
app_dir = os.path.join(current_dir, 'app')
if not os.path.exists(app_dir):
    print(f"ERROR: 'app' directory not found at {app_dir}")
    sys.exit(1)

from app import create_app  # imported after sys.path modification

# Create the Flask application using the factory function
app = create_app()

if __name__ == '__main__':
    # Run the Flask development server. Bind to all interfaces so it is
    # reachable externally if needed. Note that in production a WSGI server
    # should be used instead of the built-in development server.
    app.run(debug=True, host='0.0.0.0', port=4000)