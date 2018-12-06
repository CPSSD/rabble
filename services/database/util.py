def equivalent_filter(entry, defaults=[]):
    return entry_to_filter(entry, defaults, " = ?")


def not_equivalent_filter(entry, defaults=[]):
    return entry_to_filter(entry, defaults, ' IS NOT ""')


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

def entry_to_update(entry):
    """
    entry_to_update converts an entry to the set part of a sql query.

    This is intended to be used with entry_to_filter to produce a full query.

    For example:
      sql = "UPDATE users SET " update_clause + " WHERE " +  filter_clause

    Arguments:
      - entry: A proto message entry

    Returns:
      The SET part of an update SQL query and a list of values.

      For example:
         "bio = ?, display_name = ?" ["my bio", "my name"]
    """
    fields = entry.ListFields()
    update_list = [f.name + " = ?" for f, _ in fields]
    return ', '.join(update_list), [v for _, v in fields]
