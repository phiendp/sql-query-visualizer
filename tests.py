import unittest
from parser import Parser


class QueryParserTests(unittest.TestCase):

    def setUp(self):
        self.parser = Parser()

    def test_parse_simple_query_with_one_cte(self):
        query = """
            WITH user_orders AS (
              select
              user_id,
              count(1) as order_count
              from orders O
              where O.created_at > NOW() - INTERVAL '30 days'
              group by 1
            )
            select
              order_count,
              count(1) as num_users
            from user_orders
            group by 1
            order by 1
        """

        result = self.parser.process(query)
        expected = '{"name": "result", "children": [{"name": "user_orders", "children": [{"name": "orders"}]}]}'

        assert result == expected

    def test_parse_query_with_multiple_ctes(self):
        query = """
            with daily_users as (
              select
                created_at::date as date_d,
                count(1) as new_users
              from users
              group by 1
            ), daily_products as (
              select
                created_at::date as date_d,
                count(1) as new_users
              from products
              group by 1
            ), daily_reviews as (
              select
                created_at::date as date_d,
                count(1) as new_users
              from reviews
              group by 1
            )
            select
              U.date_d,
              U.new_users,
              P.new_products,
              R.new_reviews
            from daily_users U, daily_products P, daily_reviews R
            where U.date_d = P.date_d
              and U.date_d = R.date_d
            order by 1 DESC
        """

        result = self.parser.process(query)
        expected = '{"name": "result", "children": [{"name": "daily_users", "children": [{"name": "users"}]}, {"name": "daily_products", "children": [{"name": "products"}]}, {"name": "daily_reviews", "children": [{"name": "reviews"}]}]}'

        assert result == expected


if __name__ == '__main__':
    unittest.main()
