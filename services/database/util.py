def entry_to_filter(entry, defaults=[]):
    """
    entry_to_filter converts an entry to a filter usable in sqlite3.

    Arguments:
      - entry: A proto message entry.
      - defualts: a list of name, value tuples that indicate default values
        to include in the filter.
        For example, if you wanted host="" to be included in the query:
          defaults=[(host="")]

    Returns:
      A filter clause and a list of values.
    """
    fields = entry.ListFields()
    names = set([f.name for f, _ in fields])

    filter_list = [f.name + ' = ?' for f, _ in fields]
    for name, _ in defaults:
        if name not in names:
            filter_list.append(name + ' = ?')

    values = [v for _, v in fields]

    for name, value in defaults:
        if name not in names:
            values.append(value)

    filter_clause = ' AND '.join(filter_list)
    return filter_clause, values
