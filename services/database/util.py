def entry_to_filter(entry):
    fields = entry.ListFields()
    filter_list = [f.name + ' = ?' for f, _ in fields]
    filter_clause = ' AND '.join(filter_list)
    return filter_clause, [v for _, v in fields]
