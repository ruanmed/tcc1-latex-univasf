...
def index(idx_type='normal', db='authorprof', tool='arango', db_name='authorprof', exp_id='unamed'):
  mylogger.info(f'INDEX TYPE: {idx_type}')
  mylogger.info(f'DB: {db}')
  mylogger.info(f'TOOL: {tool}')
  mylogger.info(f'DB NAME: {db_name}')
  initial = time.time()

  testTool = IndexToolManager(indexName=db_name)

  start = time.time()
  append_class_to_id = False
  if (tool == 'zettair'):
      append_class_to_id = True
  bulk = testTool.get_documents(db,
                                db_files[db]['xml_folder'],
                                db_files[db]['truth_txt'],
                                append_class_to_id)
  end = time.time()
  mylogger.info(f'get_documents {end - start}')
  mylogger.info(f'TOTAL documents {len(bulk)}')

  start = time.time()
  if (tool == 'arango'):
    documentList = testTool.bulkListGeneratorArango(bulk)
    end = time.time()
    mylogger.info(f'bulkListGeneratorArango {end - start}')
    if (idx_type == 'normal'):
      start = time.time()
      for doc in documentList:
        testTool.insertDocumentArango(doc)
      end = time.time()
      mylogger.info(f'for-loop insertDocumentArango {end - start}')
    if (idx_type == 'bulk'):
      start = time.time()
      testTool.bulkImportArango(documentList)
      end = time.time()
      mylogger.info(f'bulkImportArango {end - start}')

  if (tool == 'elastic'):
    if (idx_type == 'normal'):
      start = time.time()
      for doc in bulk:
          testTool.insertElastic(doc.pop('id'), doc)
      end = time.time()
      mylogger.info(f'for-loop insertElastic {end - start}')
    if (idx_type == 'bulk'):
      start = time.time()
      bulkBody = testTool.bulkHelperInsertGeneratorElastic(bulk)
      end = time.time()
      mylogger.info(f'bulkHelperInsertGeneratorElastic {end - start}')
      start = time.time()
      testTool.bulkHelperElastic(bulkBody)
      end = time.time()
      mylogger.info(f'bulkHelperElastic {end - start}')

    start = time.time()
    testTool.refreshElastic()
    end = time.time()
    mylogger.info(f'refreshElastic {end - start}')

  if (tool == 'zettair'):
    start = time.time()
    testTool.saveToTrecFileZettair(bulk)
    end = time.time()
    mylogger.info(f'saveToTrecFileZettair {end - start}')
    start = time.time()
    testTool.zettair_index()
    end = time.time()
    mylogger.info(f'zettair_index {end - start}')

  final = time.time()
  result_id = datetime.datetime.now().strftime("%Y%m%d-%H%M%S.%f")
  testTool.log_result(result_id, {
    'exp_id': exp_id,
    'variable': 'TIME_INDEX',
    'index_type': idx_type,
    'db': db,
    'tool': tool,
    'db_name': db_name,
    'value': str((final - initial)),
  })
  mylogger.info(f'index TOTAL TIME: {final - initial}')