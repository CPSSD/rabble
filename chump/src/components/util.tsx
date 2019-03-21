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
        {author}@{host}
      </Link>
    );
  }
  return userLink;
}
