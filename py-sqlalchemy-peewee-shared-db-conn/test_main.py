import os
from dotenv import load_dotenv
from peewee import Model, CharField, PostgresqlDatabase
from sqlalchemy import Column, String, MetaData, Table, create_engine
from sqlalchemy.orm import sessionmaker
import psycopg2


# Load environment variables from .env file
load_dotenv()

# Get the variables from the environment
db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')

# Create the shared psycopg2 connection
shared_connection = psycopg2.connect(
    dbname=db_name, user=db_user, password=db_password, host=db_host
)

# Configure Peewee with standard parameters, not the raw connection
peewee_db = PostgresqlDatabase(
    db_name, user=db_user, password=db_password, host=db_host
)

# Manually bind the shared connection to Peewee
peewee_db._state.set_connection(shared_connection)
peewee_db._state.closed = False  # Indicate that the DB is already connected


class User(Model):
    id = CharField(primary_key=True)
    name = CharField()

    class Meta:
        database = peewee_db


# Configure SQLAlchemy using the same shared connection
engine = create_engine("postgresql+psycopg2://", creator=lambda: shared_connection)
metadata = MetaData()
sqlalchemy_table = Table(
    "user", metadata, Column("id", String, primary_key=True), Column("name", String)
)
Session = sessionmaker(bind=engine)


def test_shared_transaction():
    metadata.create_all(bind=engine)

    with Session() as session:
        # Peewee ORM operation
        User.create(name="Peewee Entry", id="1")

        # Verify both Peewee and SQLAlchemy ORM operations
        peewee_result = User.select()
        assert len(peewee_result) == 1

        sqla_result = session.execute(sqlalchemy_table.select()).fetchall()
        assert len(sqla_result) == 1

        # SQLAlchemy ORM operation
        session.execute(sqlalchemy_table.insert().values(name="SQLAlchemy", id="2"))

        # Verify both Peewee and SQLAlchemy ORM operations
        peewee_result = User.select()
        assert len(peewee_result) == 2

        sqla_result = session.execute(sqlalchemy_table.select()).fetchall()
        assert len(sqla_result) == 2

