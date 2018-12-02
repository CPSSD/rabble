def equivalent_filter(entry, defaults=[]):
    return entry_to_filter(entry, defaults, " = ?")

def not_equivalent_filter(entry, defaults=[]):
    return entry_to_filter(entry, defaults, " != ?")

def entry_to_filter(entry, defaults, comparison):
    """
    entry_to_filter converts an entry to a filter usable in sqlite3.

    Arguments:
      - entry: A proto message entry.
      - defaults: a list of name, value tuples that indicate default values
        to include in the filter.
        For example, if you wanted host="" to be included in the query:
          defaults=[(host="")]
      - comparison: a clause comparing the name of the entry fields to it's value

    Returns:
      A filter clause and a list of values.
    """
    fields = entry.ListFields()
    names = set([f.name for f, _ in fields])

    filter_list = [f.name + comparison for f, _ in fields]
    for name, _ in defaults:
        if name not in names:
            filter_list.append(name + comparison)

    values = [v for _, v in fields]

    for name, value in defaults:
        if name not in names:
            values.append(value)

    filter_clause = ' AND '.join(filter_list)
    return filter_clause, values
