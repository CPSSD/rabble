import bcrypt
from services.proto import database_pb2

def check_password(logger, pw, pw_hash):
    try:
        return bcrypt.checkpw(pw.encode('utf-8'),
                              pw_hash.encode('utf-8'))
    except ValueError as e:
        logger.warning(
            "Password hash in DB '%s' caused an error: %s",
            pw_hash, str(e))
        return False # Invalid salt.

def get_user_and_check_pw(logger, db_stub, handle, pw):
    """
    get_user_and_check finds a user and checks their password.

    Raises:
        On a database lookup failure, raises a ValueError.

    Returns:
        Returns a tuple: (Result, Error)
        Error is a string containing details a login error.

        if their password is incorrect: returns None, Error
        if their password is correct: returns UserEntry, None
    """
    if not handle:
        err = "Received blank username"
        logger.warning(err)
        raise ValueError(err)
    if not pw:
        err = "Received blank password"
        logger.warning(err)
        raise ValueError(err)
    find_request = database_pb2.UsersRequest(
        request_type=database_pb2.UsersRequest.FIND,
        match=database_pb2.UsersEntry(
            handle=handle,
        ),
    )
    db_resp = db_stub.Users(find_request)
    if db_resp.result_type != database_pb2.UsersResponse.OK:
        err = "Error getting user from DB: " + db_resp.error
        logger.warning(err)
        raise ValueError(db_resp.error)

    elif len(db_resp.results) != 1:
        err = "Got {} users matching handle {}, expecting 1".format(
              len(db_resp.results), handle)
        logger.warning(err)
        raise ValueError("Got wrong number of users matching query")

    user = db_resp.results[0]
    if not check_password(logger, pw, user.password):
        err = "ACCESS DENIED for user %s", handle
        logger.info(err)
        return None, err

    logger.info("*hacker voice* I'm in (%s)", handle)
    return user, None
