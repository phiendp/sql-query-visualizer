import unittest
from parser import Parser


class QueryParserTests(unittest.TestCase):

    def setUp(self):
        self.parser = Parser()

    def test_parse_simple_select_query(self):
        query = """
            select a, b from users
        """

        result = self.parser.process(query)
        expected = '[{"children": [{"name": "users"}], "name": "result: a, b"}]'

        assert result == expected

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
        expected = '[{"children": [{"children": [{"name": "orders: user_id"}], "name": "user_orders: user_id, order_count"}], "name": "result: order_count, num_users"}]'

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
        expected = '[{"children": [{"children": [{"name": "users: created_at"}], "name": "daily_users: date_d, new_users"}, {"children": [{"name": "products: created_at"}], "name": "daily_products: date_d, new_users"}, {"children": [{"name": "reviews: created_at"}], "name": "daily_reviews: date_d, new_users"}], "name": "result: date_d, new_users, new_products, new_reviews"}]'
        assert result == expected


if __name__ == '__main__':
    unittest.main()
