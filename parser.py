from pg_query import Node, parse_sql
import json


class Parser(object):

    def process(self, sql):
        """
        Given a plain sql query, parse it to a tree representation.
        Then process the WITH clause to determine the CTEs.
        Then process the outermost SELECT statement for the final result, with every used CTE
        as its children
        """
        root = Node(parse_sql(sql))

        cte_expression = root[0].stmt.withClause.ctes
        ctes = self.build_ctes_from(cte_expression)

        relation_from_result = root[0].stmt.fromClause
        target_list_from_result = root[0].stmt.targetList

        result = [self.build_result_from(relation_from_result, target_list_from_result, ctes)]
        return json.dumps(result)

    def build_ctes_from(self, cte_expression):
        """
        Given a CTE expression, return a hash table with each CTE's name as key.
        And a hash table ofits children and name as value
        """
        ctes = dict()
        for cte in cte_expression:
            name = cte.ctename.value
            ctes[name] = dict()
            ctes[name]['children'] = []

            rel_expression = cte.ctequery.fromClause
            target_list = cte.ctequery.targetList

            for rel in rel_expression:
                fields_name = ','.join(self.get_fields_from(target_list))
                ctes[name]['children'].append(
                    {"name": "{}: {}".format(rel.relname.value, fields_name)})

            fields = self.get_fields_from(target_list, for_outer=True)
            ctes[name]['name'] = "{}: {}".format(name, ", ".join(fields))
        return ctes

    def build_result_from(self, relation_from_result, target_list_from_result, ctes):
        """
        Given the outermost SELECT statement, return a hash table that contains the query's name and
        all of its children (the stored CTEs that are used in the query)
        """
        result = dict()
        result['children'] = []

        for rel in relation_from_result:
            name = rel.relname.value
            if name not in ctes:
                result['children'].append(name)
            else:
                result['children'].append(ctes[name])

        fields = self.get_fields_from(target_list_from_result, for_outer=True)
        result['name'] = 'result: {}'.format(', '.join(fields))

        return result

    def get_fields_from(self, target_list, for_outer=False):
        """
        Return a list of retrieved field from the fromClause
        """
        fields = []
        for target in target_list:
            tag = target.val.node_tag
            if tag == 'ColumnRef':
                fields.append(target.val.fields[-1].str.value)
            elif (tag == 'FuncCall' or tag == 'TypeCast') and for_outer:
                fields.append(target.name.value)
            elif tag == 'TypeCast':
                fields.append(target.val.arg.fields[0].str.value)
        return fields
