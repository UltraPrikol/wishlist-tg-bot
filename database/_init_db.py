from sqlalchemy import create_engine
from dotenv import dotenv_values
from models import Base


config = dotenv_values('../.env')

database_url = config['DATABASE_URL']
engine = create_engine(database_url, echo=True, pool_recycle=7200)

Base.metadata.create_all(engine)
