# -*- coding: utf-8 -*-

def index():
    redirect(URL('examples'))
    return dict()

def examples():
    return dict()

def main():
    return dict()

def api():
    """
    $ curl http://127.0.0.1:8000/collection/default/api
    $ curl http://127.0.0.1:8000/collection/default/api/book
    $ curl http://127.0.0.1:8000/collection/default/api/book?page=1&per_page=20
    $ curl http://127.0.0.1:8000/collection/default/api/book?search=title contains "the"
    $ curl http://127.0.0.1:8000/collection/default/api/bookcase
    $ curl http://127.0.0.1:8000/collection/default/api/bookcase/1
    $ curl -X POST -d 'title=GEB' http://127.0.0.1:8000/collection/default/api/book
    {"row": {"id": 91}}
    $ curl -X DELETE http://127.0.0.1:8000/collection/default/api/book/93 
    {"count": 1}
    $ curl -X DELETE http://127.0.0.1:8000/collection/default/api/book/93
    {"count": 0}
    """
    from dbapi import DBAPI
    api = DBAPI(db)
    # allow GET for table auth_user
    api.add_policy('auth_user','GET')
    # allow GET for table bookstore and allow joining other tables
    api.add_policy('bookcase','GET', join=[
            dict(field=db.auth_user.id),
            dict(field=db.book.bookcase)
            ])
    # allow GET on table book, also allow complex searches by keywords
    def complex_search(keywords):
        return (db.book.title.contains(keywords)|
                ((db.book.bookcase==db.bookcase.id)&
                 (db.bookcase.name.contains(keywords))))
    api.add_policy('book','GET',
                   join=[dict(field=db.auth_user.id), dict(field=db.bookcase.id)],
                   constraint=(db.book.bookcase<4),
                   keywords_search=complex_search)
    # for logged in users allow POSTing and DELETEing book on the 3rd bookcase.
    if auth.user or request.is_local:
        # can only post to bookcase 3
        db.book.bookcase.default = 3
        db.book.bookcase.writable = False
        # record who posted it
        db.book.posted_by.default = auth.user_id or 1
        db.book.bookcase.writable = False
        api.add_policy('book','PUT')
        api.add_policy('book','POST')
        api.add_policy('book','DELETE')
    # respond to API call
    return api.process()

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/bulk_register
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    also notice there is http://..../[app]/appadmin/manage/auth to allow administrator to manage users
    """
    return dict(form=auth())


@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


