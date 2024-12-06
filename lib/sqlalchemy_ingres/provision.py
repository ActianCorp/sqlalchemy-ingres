from sqlalchemy.testing.provision import temp_table_keyword_args


@temp_table_keyword_args.for_db("ingres")
def _ingres_temp_table_keyword_args(cfg, eng):
    return {}
