import sys
sys.path.insert(0,'..')

from depends import *

host=Table('host', Base.metadata,
    Column('id', Integer, ForeignKey('system.id',
                                     ondelete='CASCADE',
                                     name='host_system_fk'), primary_key=True),
    Column('machine_id', Integer,
           ForeignKey('machine.id', name='host_machine_fk'), nullable=False),
    Column('domain_id', Integer,
           ForeignKey('domain.id', name='host_domain_fk'), nullable=False),
    Column('archetype_id',Integer,
           ForeignKey('archetype.id', name='host_arch_fk'), nullable=False),
    Column('status_id', Integer,
           ForeignKey('status.id', name='host_status_fk'), nullable=False))

