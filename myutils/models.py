from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from myutils.API_KEYS import DATABASE_URI

engine = create_engine(DATABASE_URI)
Base = declarative_base()
Session = sessionmaker(bind=engine)

class Lists(Base):
    __tablename__ = "lists"
    id = Column(Integer, primary_key = True)
    title = Column(String(200))
    author = Column(String) #author_id
    author_name = Column(String)
    created = Column(DateTime, default = datetime.now())
    private = Column(Boolean, default = False)

    rel_tasks = relationship('Tasks', back_populates='rel_list', cascade="all, delete, delete-orphan", lazy=True)

    def __repr__(self):
        return f'<List {self.id}, Title {self.title}, Author {self.author}, Created {self.created}, Private {self.private}>'

class Tasks(Base):
    __tablename__ = "tasks"
    taskID = Column(Integer, primary_key = True)
    listID = Column(Integer, ForeignKey('lists.id'), nullable=False)
    taskItem = Column(Text)
    number = Column(Integer)
    status = Column(String, default= "<:notdone:926280852856504370>")

    rel_list = relationship('Lists', back_populates='rel_tasks')

    def __repr__(self):
        return f'<Task: {self.taskItem}>'

def recreate():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print("database recreated")
