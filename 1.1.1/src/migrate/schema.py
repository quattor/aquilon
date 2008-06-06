from depends import *

def get_id_col(name):
    return Column('id', Integer, Sequence('%s_seq'%(name)),primary_key=True)

def get_date_col():
    return Column('creation_date', DateTime, default = datetime.now)

def get_comment_col():
    return Column('comments', String(255), nullable = True)
