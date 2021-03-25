from django.db import connection, reset_queries

def query_count_context(request):
    sqltime = 0 # Variable to store execution time
    for query in connection.queries:
        sqltime += float(query["time"])  # Add the time that the query took to the total
    n = len(connection.queries)
    #for query in connection.queries:
    #    print("--------")
    #    print(f"Time: {query['time']}")
    #    print(f"Query: {query['sql']}")
    reset_queries()

    return {'query_num':n, 'time':str(sqltime)}