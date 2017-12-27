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

    def test_parse_multiple_cte_with_join(self):
        query = """
            with a as (
              select a1 from users
            ), b as (
              select a1 as b1 from a
            )
            select
              a.a1,
              b.b1
            from a
            left join b on a.a1 = b.b1
        """
        result = self.parser.process(query)
        expected = '[{"children": [{"name": "a"}, {"name": "b"}], "name": "result: a1, b1"}]'
        assert result == expected

    def test_simple_joins_query(self):
        query = """
            SELECT
              S.pid,
              age(clock_timestamp(), query_start),
              usename,
              query,
              L.mode,
              L.locktype,
              L.granted
            FROM pg_stat_activity S
            inner join pg_locks L on S.pid = L.pid
            order by L.granted, L.pid DESC
        """

        result = self.parser.process(query)
        expected = '[{"children": [{"name": "pg_stat_activity"}, {"name": "pg_locks"}], "name": "result: pid, age, usename, query, mode, locktype, granted"}]'
        assert result == expected

    def test_sub_queries(self):
        query = """
            select
              S.date_d,
              S.new_users,
              R.renewals,
              L.total_charged,
              L.total_charging_attempts
            from (
                select
                  date(S.created_at) AS date_d,
                  count(distinct S.user_id) AS new_users
                from tbl_subscribers S
                where S.created_at >= '2017-12-20' -- {{ date_start }}
                  and S.created_at < '2017-12-21' -- {{ date_end }}
                  and S.is_subscribed = 1
                group by 1
            ) S, (
                select
                  date(R.created_at) AS date_d,
                  count(distinct R.user_id) as renewals
                from tbl_renewal R
                where R.created_at >= '2017-12-20' -- {{ date_start }}
                  and R.created_at < '2017-12-21' -- {{ date_end }}
                  and R.status = 1
                group by 1
                order by 1 desc
            ) R, (
                select
                  date(L.created_at) AS date_d,
                  count(distinct (CASE when status_code_id=2 THEN L.user_id ELSE NULL END)) as total_charged,
                  count(distinct L.user_id) as total_charging_attempts
                from tbl_charging_logs L
                where L.created_at >= '2017-12-20'
                  and L.created_at < '2017-12-21'
                group by 1
                order by 1 desc
            ) L
            where S.date_d = R.date_d
              and S.date_d = L.date_d
            order by 1 desc
        """

        result = self.parser.process(query)
        expected = '[{"children": [{"name": "tbl_subscribers: date_d,new_users"}, {"name": "tbl_renewal: date_d,renewals"}, {"name": "tbl_charging_logs: date_d,total_charged,total_charging_attempts"}], "name": "result: date_d, new_users, renewals, total_charged, total_charging_attempts"}]'
        assert result == expected


if __name__ == '__main__':
    unittest.main()
