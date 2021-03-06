def equivalent_filter(entry, defaults=[], deferred={}):
    return entry_to_filter(entry, defaults, " = ?", deferred)


def not_equivalent_filter(entry, defaults=[], deferred={}):
    return entry_to_filter(entry, defaults, ' IS NOT ""', deferred)

def build_filter_list(fields, comp, deferred):
    return [f.name + comp for f, _ in fields if f.name not in deferred]

class DONT_USE_FIELD:
    pass

def entry_to_filter(entry, defaults, comparison, deferred={}):
    """
    entry_to_filter converts an entry to a filter usable in sqlite3.

    Arguments:
      - entry: A proto message entry.
      - defaults: a list of name, value tuples that indicate default values
        to include in the filter.
        For example, if you wanted test="" to be included in the query:
          defaults=[("test", "")]
      - comparison: a clause comparing the name of the entry fields to it's value
      - deferred: a map of proto entry names to defer a value conversion to.
        The keys of this map are the names of any entry where the value is to
        be deferred to their explicit handling function.
        The value is a function that takes the PostEntry proto and the
        comparison string (e.g. " = ?") as arguments and returns the full
        comparison to use (e.g. "test = ?") and the value to be substituted.
        If the field shouldn't be added to the filter return the DONT_USE_FIELD
        sentinel in place of the value.

    Returns:
      A filter clause and a list of values.
    """
    fields = entry.ListFields()

    names = {f.name for f, _ in fields if f.name not in deferred}
    filter_list = build_filter_list(fields, comparison, deferred)

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
        filt, val = deferred[name](entry, comparison)
        if val is DONT_USE_FIELD:
            continue
        filter_list.append(filt)
        names.add(name)
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
        The value is a function that takes the PostEntry proto and the
        comparison string (e.g. " = ?") as arguments and returns the full
        comparison to use (e.g. "test = ?") and the value to be substituted.
        If the field shouldn't be added to the filter return the DONT_USE_FIELD
        sentinel in place of the value.

    Returns:
      The SET part of an update SQL query and a list of values.

      For example:
         "bio = ?, display_name = ?" ["my bio", "my name"]
    """
    fields = entry.ListFields()
    update_list = build_filter_list(fields, " = ?", deferred)

    values = []
    handle_deferred = []
    for f, v in fields:
        if f.name not in deferred:
            values.append(v)
        else:
            handle_deferred.append(f.name)

    for name in handle_deferred:
        filt, val = deferred[name](entry, " = ?")
        if val is DONT_USE_FIELD:
            continue
        update_list.append(filt)
        values.append(val)

    return ', '.join(update_list), values
