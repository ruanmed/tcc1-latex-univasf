...
ir_top_k = 100
...
testTool = IndexToolManager(
    indexName=str(hyperpartisan_db_name), top_k=ir_top_k)
...
def gloveVectorize(glove, text):
    ...
    for text_id, t in enumerate(text):
        ...
        if (exp_dict['add_ir_variables']):
            initial = time.time()
            ign_first = ignore_first_result and (text_id in id1)
            if (exp_dict['tool'] == 'arango'):
                ir_variables = testTool.arango_get_IR_variables(
                    t, 'true', ignore_first_result=ign_first)
            elif (exp_dict['tool'] == 'elastic'):
                ir_variables = testTool.elastic_get_IR_variables(
                    t, 'true', ignore_first_result=ign_first)
            elif (exp_dict['tool'] == 'zettair'):
                ir_variables = testTool.zettair_get_IR_variables(
                    t, 'true', interactive=False,
                    ignore_first_result=ign_first)
            final = time.time()
            time_query_list.append(float(final-initial))
            ir_vars_dict = [
                ir_variables['CLASS_0_BM25_AVG'],
                ir_variables['CLASS_0_BM25_COUNT'],
                ir_variables['CLASS_0_BM25_SUM'],
                ir_variables['CLASS_1_BM25_AVG'],
                ir_variables['CLASS_1_BM25_COUNT'],
                ir_variables['CLASS_1_BM25_SUM'],
            ]
        ...