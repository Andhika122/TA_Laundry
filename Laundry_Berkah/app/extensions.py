"""
Shared Flask extension instances.

Keeping extensions in a small module prevents duplicate objects when the app
package is reloaded during tests or development tooling.
"""
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
