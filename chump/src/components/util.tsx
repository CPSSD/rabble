import * as React from "react";
import { Link } from "react-router-dom";

export function GenerateUserLinks(authorId: number, author: string, host: string) {
  let userLink = (
    <Link to={`/@${authorId}`} className="author-handle">
      @{author}
    </Link>
  );
  if (host !== null && host !== "" && typeof host !== "undefined") {
    userLink = (
      <Link to={`/@${authorId}`} className="author-handle">
        {author}@{RemoveProtocol(host)}
      </Link>
    );
  }
  return userLink;
}

export function RemoveProtocol(host: string) {
  if (host.startsWith("https://")) {
    host = host.substring(8)
  } else if (host.startsWith("http://")) {
    host = host.substring(7)
  }
  return host
}
