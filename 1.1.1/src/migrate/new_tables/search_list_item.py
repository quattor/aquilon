class SearchListItem(Base):
    """ Association object for location types to various lists for
        searching against service mapping. """

    __table__ = Table('search_list_item', Base.metadata,
    Column('id', Integer, Sequence('sli_seq'), primary_key=True),
    Column('location_search_list_id', Integer,
        ForeignKey('location_search_list.id', ondelete='CASCADE',
            name='sli_list_fk'), nullable=False),
    Column('location_type_id', Integer,
           ForeignKey('location_type.id', ondelete='CASCADE',
               name='sli_loc_typ__fk'), nullable=False),
    Column('position', Integer, nullable=False),
    Column('creation_date', DateTime, default=datetime.now),
    Column('comments', String(255), nullable=True),
    UniqueConstraint('id','location_type_id',name='sli_loc_typ_uk'),
    UniqueConstraint('location_type_id','position',name='sli_loc_typ_pos_uk'))

    location_search_list = relation(LocationSearchList, backref='items')
    location_type        = relation(LocationType)

    def __repr__(self):
        return (self.__class__.__name__ + ' ' + self.location_type.type +
                ' position: ' + str(self.position))
