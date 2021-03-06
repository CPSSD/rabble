import * as React from "react";
import { Link } from "react-router-dom";

export function GetCustomCSS(authorId: number, enable: boolean) {
  if (!enable) {
    return false;
  }

  return (
    <link
      rel="stylesheet"
      type="text/css"
      href={`/c2s/${authorId}/css`}
    />
  );
}

export function GenerateUserLinks(author: string, host: string, displayName: string, divClassName: string) {
  let userAddress = `/@${author}`;
  let userHandleHost = (
    <Link to={userAddress} className="author-handle">
      @{author}
    </Link>
  );

  if (host !== null && host !== "" && typeof host !== "undefined") {
    const normalHost = RemoveProtocol(host);
    userAddress = `/@${author}@${normalHost}`;
    userHandleHost = (
      <Link to={userAddress} className="author-handle">
        @{author}@{normalHost}
      </Link>
    );
  }
  const userLinks = (
    <div className={divClassName}>
      <Link to={userAddress} className="author-displayname">
        {displayName}
      </Link><br/>
      {userHandleHost}
    </div>
  );
  return userLinks;
}

export function RemoveProtocol(host: string) {
  if (host.startsWith("https://")) {
    host = host.substring(8);
  } else if (host.startsWith("http://")) {
    host = host.substring(7);
  }
  return host;
}
