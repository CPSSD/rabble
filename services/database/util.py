def equivalent_filter(entry, defaults=[], deferred={}):
    return entry_to_filter(entry, defaults, " = ?", deferred)


def not_equivalent_filter(entry, defaults=[], deferred={}):
    return entry_to_filter(entry, defaults, ' IS NOT ""', deferred)


def entry_to_filter(entry, defaults, comparison, deferred={}):
    """
    entry_to_filter converts an entry to a filter usable in sqlite3.

    Arguments:
      - entry: A proto message entry.
      - defaults: a list of name, value tuples that indicate default values
        to include in the filter.
        For example, if you wanted host="" to be included in the query:
          defaults=[(host="")]
      - comparison: a clause comparing the name of the entry fields to it's value
      - deferred: a map of proto entry names to defer a value conversion to.
        The keys of this map are the names of any entry where the value is to
        be deferred to their explicit handling function.
        The value is a function that takes as an argument as entry, and can
        return either None (meaning do not add the field to the filter) or
        a primitive value suitable for database use.

    Returns:
      A filter clause and a list of values.
    """
    fields = entry.ListFields()

    names = set()
    for f, _ in fields:
        if f.name in deferred:
            continue
        names.add(f.name)

    filter_list = []
    for f, _ in fields:
        if f.name in deferred:
            continue
        filter_list.append(f.name + comparison)

    for name, _ in defaults:
        if name not in names:
            filter_list.append(name + comparison)

    values = []
    handle_deferred = []
    for f, v in fields:
        if f.name not in deferred:
            values.append(v)
        else:
            handle_deferred.append(f.name)

    for name in handle_deferred:
        val = deferred[name](entry)
        if val is None:
            continue
        # We need to make sure we're not adding twice
        # in the case of having a default deferred value
        if f.name not in filter_list:
            filter_list.append(f.name + comparison)
            # we ensure that the nmae is ensure we dont
            # add another value
            names.add(f.name)
        values.append(val)

    for name, value in defaults:
        if name not in names:
            values.append(value)

    filter_clause = ' AND '.join(filter_list)
    return filter_clause, values

def entry_to_update(entry, deferred={}):
    """
    entry_to_update converts an entry to the set part of a sql query.

    This is intended to be used with entry_to_filter to produce a full query.

    For example:
      sql = "UPDATE users SET " + update_clause + " WHERE " + filter_clause

    Arguments:
      - entry: A proto message entry
      - deferred: a map of proto entry names to defer a value conversion to.
        The keys of this map are the names of any entry where the value is to
        be deferred to their explicit handling function.
        The value is a function that takes as an argument as entry, and can
        return either None (meaning do not add the field to the filter) or
        a primitive value suitable for database use.

    Returns:
      The SET part of an update SQL query and a list of values.

      For example:
         "bio = ?, display_name = ?" ["my bio", "my name"]
    """
    fields = entry.ListFields()

    update_list = []
    for f, _ in fields:
        if f.name in deferred:
            continue
        update_list.append(f.name + " = ?")

    values = []
    handle_deferred = []
    for f, v in fields:
        if f.name not in deferred:
            values.append(v)
        else:
            handle_deferred.append(f.name)

    for name in handle_deferred:
        val = deferred[name](entry)
        if val is None:
            continue
        update_list.append(f.name + " = ?")
        values.append(val)

    return ', '.join(update_list), values
