import copy
import json
import urllib

# table
# fields for table, referencing, referenced by
# items

class APIMaker(object):

    MAPS = {'<=':lambda a,b: a<=b,
            '>=':lambda a,b: a>=b,
            '<':lambda a,b: a<b,
            '>':lambda a,b: a>b,
            '==':lambda a,b: a==b,
            '!=':lambda a,b: a!=b,
            '<>':lambda a,b: a!=b,
            '~':lambda a,b: a.lower()==b.lower(),
            '=':lambda a,b: a==b,
            ' in ':lambda a,b: a.belongs(b),
            ' contains ':lambda a,b: a.contains(b),
            ' startswith ':lambda a,b: a.startswith(b)}

    def __init__(self, db):
        self.db = db
        self.policies = {}
        self.max_per_page = 100
        self.default_per_page = 20

    def add_policy(self, tablename, method,
                   constraint = None,
                   join = None,
                   keywords_search = None):
        if not tablename in self.policies:
            self.policies[tablename] = {}
        self.policies[tablename][method] = {
            'constraint':constraint,
            'join':join,
            'fields':None,
            'keywords_search':keywords_search,
            }

    @staticmethod
    def parse_search_query(table, policy, search):
        import ast
        if not search:
            return None, None
        parsed_items = []
        items = map(lambda x: x.strip(), search.split(' and '))
        for item in items:
            negate = item.startswith('not ')
            if negate: item.strip('not').lstrip()
            for key in APIMaker.MAPS:
                parts = item.split(key,1)
                if len(parts)==2:
                    op = APIMaker.MAPS[key]
                    try:
                        field = table[parts[0]]
                    except:
                        return None, 'invalid field name: "%s"' % parts[0]
                    try:
                        value = ast.literal_eval(parts[1])
                    except:
                        return None, 'invalid field value "%s" (try quote it)' % parts[1]
                    break
            else:
                return None, 'invalid operator in: "%s"' % item
            q = op(field, value)
            if negate: q = ~q
            parsed_items.append(q)
            return reduce(lambda a,b: a&b, parsed_items), None

    @staticmethod
    def parse_keywords_query(table, policy, keywords):
        keywords_search = policy.get('keywords_search') or []
        keywords = (keywords or '').strip()
        if not keywords:
            return None, None
        if isinstance(keywords_search, list):
            queries = []
            for token in keywords.split():
                subqueries = [f.contains(token) for f in keywords_search]
                queries.append(reduce(lambda a,b:a|b, subqueries))
            query = reduce(lambda a,b:a&b, queries)
        elif  callable(keywords_search):
            query = keywords_search(keywords)
        else:
            return None, "keywords search not supported"
        return query, None

    @staticmethod
    def parse_sort(table, sort):
        if not sort:
            return None, None
        names = sort.split(',')
        invalid_names = filter(lambda x: x.lstrip('~') not in table.fields, names)
        if invalid_names:
            return None, 'invalid sort fields: %s' % ','.join(invalid_names)
        orderby =[~table[x[1:]] if x[0]=='~' else table[x] for x in sort.split(',')]
        return orderby, None

    def handle_request(self, base_url, method, tablename=None, row_id=None, vars=None):
        db = self.db
        # these are the policies to be enforced by the API
        policies = self.policies
        # these are the request variables (GET or POST)
        vars = vars or {}
        # default return value
        data = {'error': 'bad request', 'status':400}
        # if not tablename, return a list of tablesnames and their policies
        if not tablename:
            items = [{'name':name} for name, policy in policies.items()]
            data = {'tables':items, 'href':base_url+'/{name}/@metadata'}
        else:
            # if there is a tablename but does not match a policty, error
            if not tablename in policies or not method in policies[tablename]:
                data = {'error': 'not authorized', 'status':404}
            elif method == 'GET':
                # deal with GET requests
                table = db[tablename]
                policy = policies[tablename][method]
                if row_id == '@metadata':
                    # user requested metadata about the table
                    fields = [{'name':f.name,
                               'type':f.type,
                               'writable':f.writable,
                               'notnull':f.notnull,
                               'default':f.default,
                               'options':getattr(f,'options',None),
                               'regex':getattr(f,'regex',None),
                               } for f in table if f.readable and not f.type=='password']
                    methods = policies[tablename].keys()
                    examples = [
                        base_url+'/'+tablename,
                        base_url+'/'+tablename+'/@metadata',
                        base_url+'/'+tablename+'?page=1&per_page=20',
                        base_url+'/'+tablename+'?search=id<10',
                        base_url+'/'+tablename+'?keywords=hello world',
                        base_url+'/'+tablename+'?sort=~id',
                        base_url+'/'+tablename+'/{id}',
                        base_url+'/'+tablename+'/{id}?joined=true'
                        ]
                    data = {'name':tablename,
                            'fields':fields,
                            'methods':methods,
                            'examples':examples}
                elif not row_id:
                    # user requested a list of rows
                    url = base_url + '/' + tablename
                    # maybe the user specified a search query
                    search = vars.get('search')
                    query_search, err = self.parse_search_query(table, policy, search)
                    if err: return {'error':err}
                    keywords = vars.get('keywords')
                    query_kwords, err = self.parse_keywords_query(table, policy, keywords)
                    if err: return {'error':err}
                    # maybe the user specified an ordering
                    orderby, err = self.parse_sort(table, vars.get('sort'))
                    if err: return {'error':err}
                    # maybe the user specified a page (defaults 20 items per page)
                    try:
                        page = max(1, int(vars.get('page') or 1))
                    except: return {'error': 'invalid page attribute'}
                    try:
                        per_page = min(self.max_per_page, int(vars.get('per_page') or
                                                              self.default_per_page))
                    except: return {'error': 'invalid per_page attribute'}
                    limitby = ((page-1)*per_page, page*per_page)
                    # maybe the user specified a constraint
                    query = policy.get('constraint', None)
                    # build the final query
                    if query_search: query = query & query_search if query else query_search
                    if query_kwords: query = query & query_kwords if query else query_kwords
                    if not query: query = table
                     # figure out which fields are accessible to the user
                    fields = policy.get('fields', None)
                    if not fields:
                        fields = [f for f in table
                                  if f.readable and not f.type in ('password','text','blob')]
                    else:
                        fields = [table[f] if isinstance(f,str) else f for f in fields]
                    # get the records
                    rows = db(query).select(*fields,limitby=limitby, orderby=orderby, distinct=True)
                    # join additional tables (optional)
                    if vars.get('joined')=='true':
                        for join_args in policy.get('join') or []:
                            rows.join(**join_args)
                    # count the total number of records
                    count = db(query).count()
                    # build response
                    data = {'rows':rows, 'count':count, 'href':url+'/{id}'}
                    # add links to next and previus pages
                    # FIX THIS!!
                    if count and page>1:
                        min_page = min(page-1, (count-1)/per_page+1)
                        new_vars = copy.copy(vars)
                        new_vars.update(page=min_page, per_page=per_page)
                        q = [k+'='+urllib.quote(str(v)) for k,v in new_vars.iteritems()]
                        data['previous'] = url+'?'+'&'.join(q)
                    if count and page*per_page<count:
                        new_vars = copy.copy(vars)
                        new_vars.update(page=page+1, per_page=per_page)
                        q = [k+'='+urllib.quote(str(v)) for k,v in new_vars.iteritems()]
                        data['next'] = url+'?'+'&'.join(q)
                elif str(row_id).isdigit():
                    # the user requested an individual record
                    row_id = int(row_id)
                    fields = policy.get('fields', None)
                    if not fields:
                        fields = [f for f in table if f.readable and not f.type in ('password',)]
                    else:
                        fields = [table[f] if isinstance(f,str) else f for f in fields]
                    # build the query
                    query = table._id == row_id
                    constraint = policy.get('constraint', None)
                    if constraint: query = query & constraint
                    rows = db(query).select(*fields)
                    if vars.get('joined')=='true':
                        for join_args in policy.get('join') or []:
                            rows.join(**join_args)
                    data = {'row': rows[0]} if rows else {}
            elif method in 'POST' and not row_id:
                table = db[tablename]
                policy = policies[tablename][method]
                fields = {}
                for key, value in vars.iteritems():
                    if not key in table.fields or not table[key].writable:
                        data = {'error':'unable to post field %s' % key, 'status':400}
                        break
                    fields[key] = value
                else:
                    try:
                        id = table.insert(**fields)
                        data = {'row': {'id': id}}
                    except:
                        pass
            elif method == 'PUT' and row_id and str(row_id).isdigit():
                # editing an existing record
                table = db[tablename]
                policy = policies[tablename][method]
                query = table._id==row_id
                constraint = policy.get('constraint', None)
                if constraint: query = query & constraint
                fields = {}
                # check user is allowed to post those fields
                for key, value in vars.iteritems():
                    if not key in table.fields or not table[key].writable:
                        data = {'error':'unable to post field %s' % key, 'status':400}
                        break
                    fields[key] = value
                else:
                    try:
                        n = db(query).update(**fields)
                        data = {'count':n}
                    except: pass
            elif method == 'DELETE' and row_id and str(row_id).isdigit():
                # delete an existing record
                table = db[tablename]
                policy = policies[tablename][method]
                query = table._id==row_id
                constraint = policy.get('constraint', None)
                if constraint: query = query & constraint
                try:
                    n = db(query).delete()
                    data = {'count':n}
                except: pass
            else:
                data = {'error':'method not allowed', 'status':405}
        return data

    def process(self):
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
        # this is the only part web2py specific!
        from gluon import URL, current
        request, response = current.request, current.response
        res = self.handle_request(URL(), request.env.request_method,
                                  request.args(0), request.args(1), request.vars)
        if 'status' in res and res['status'] != 200:
            response.status = res['status']
        response.headers['Content-Type'] = 'application/json'
        return response.json(res, indent=2)+'\n'
