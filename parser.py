from pg_query import Node, Missing, parse_sql
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
        # for node in root.traverse():
        #     print(node)

        statement = root[0].stmt

        ctes = dict()
        if statement.withClause is not Missing:
            cte_expression = statement.withClause.ctes
            ctes = self.build_ctes_from(cte_expression)

        from_clause = statement.fromClause
        target_list = statement.targetList
        result = [self.build_result_from(from_clause, target_list, ctes)]
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

    def build_result_from(self, from_clause, target_list, ctes):
        """
        Given the outermost SELECT statement, return a hash table that contains the query's name and
        all of its children (the stored CTEs that are used in the query)
        """
        result = dict()
        result['children'] = []

        for rel in from_clause:
            if rel.node_tag == 'JoinExpr':
                left_arg = rel.larg.relname.value
                right_arg = rel.rarg.relname.value
                result['children'].append({"name": left_arg})
                result['children'].append({"name": right_arg})
                continue

            name = rel.relname.value
            if name not in ctes:
                result['children'].append({"name": name})
            else:
                result['children'].append(ctes[name])

        fields = self.get_fields_from(target_list, for_outer=True)
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
            elif tag == 'FuncCall' and for_outer:
                self.process_func_call_query(target, fields)
            elif tag == 'TypeCast' and for_outer:
                fields.append(target.name.value)
            elif tag == 'TypeCast':
                fields.append(target.val.arg.fields[0].str.value)
        return fields

    def process_func_call_query(self, target, fields):
        if target.name is not Missing:
            fields.append(target.name.value)
        else:
            fields.append(target.val.funcname[0].str.value)
