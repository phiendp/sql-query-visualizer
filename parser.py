from pg_query import prettify


class Parser(object):

    def process(self, sql):
        return prettify(sql)
