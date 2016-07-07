db.define_table(
    'bookcase',
    Field('name'),
    Field('created_by','reference auth_user'))
db.define_table(
    'book',
    Field('title'),
    Field('bookcase','reference bookcase'),
    Field('posted_by','reference auth_user'))

if db(db.auth_user).isempty():
    import random
    from gluon.contrib.populate import populate
    populate(db.auth_user,10)    
    for name in ('Red','Green','Blue'):
        db.bookcase.insert(name=name, created_by=random.choice(range(1,11)))
        populate(db.book,30)
        

