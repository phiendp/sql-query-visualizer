from pg_query import Node, parse_sql
import json


class Parser(object):

    def update_target_list(self, target_list):
        fields = []
        for target in target_list:
            if target.val.node_tag == 'ColumnRef':
                fields.append(target.val.fields[-1].str.value)
            elif target.val.node_tag == 'FuncCall':
                fields.append(target.name.value)
        return fields

    def build_ctes_from(self, cte_expression):
        ctes = dict()
        for cte in cte_expression:
            name = cte.ctename.value
            ctes[name] = dict()
            ctes[name]['children'] = []

            rel_expression = cte.ctequery.fromClause
            for rel in rel_expression:
                ctes[name]['children'].append({"name": rel.relname.value})

            target_list = cte.ctequery.targetList
            fields = self.update_target_list(target_list)
            ctes[name]['name'] = "{} - {}".format(name, ", ".join(fields))
        return ctes

    def build_result_from(self, rel_result, target_list, ctes):
        result = dict()
        result['children'] = []

        for rel in rel_result:
            name = rel.relname.value
            if name not in ctes:
                result['children'].append(name)
            else:
                result['children'].append(ctes[name])

        fields = self.update_target_list(target_list)

        result['name'] = 'result: {}'.format(', '.join(fields))

        return result

    def process(self, sql):
        root = Node(parse_sql(sql))

        cte_expression = root[0].stmt.withClause.ctes
        ctes = self.build_ctes_from(cte_expression)

        rel_result = root[0].stmt.fromClause
        target_list = root[0].stmt.targetList

        result = [self.build_result_from(rel_result, target_list, ctes)]
        return json.dumps(result)
