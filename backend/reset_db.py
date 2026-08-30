import os
import sys

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))
# Also need to set pythonpath properly so app.core is found
sys.path.append(os.path.dirname(__file__))

from app.core.database import engine
from app.models.academic import Base

print("Dropping all tables...")
Base.metadata.drop_all(bind=engine)
print("Creating all tables...")
Base.metadata.create_all(bind=engine)
print("Done!")
