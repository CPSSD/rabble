import * as Promise from "bluebird";
import * as superagent from "superagent";

interface IBlogPost {
  author: string;
  author_id: number;
  bio: string;
  body: string;
  global_id: number;
  image: string;
  likes_count: number;
  is_liked: boolean;
  published: string;
  title: string;
  is_followed: boolean;
  is_shared: boolean;
}

export interface IFeedResponse {
  post_body_css: string;
  post_title_css: string;
  results: IBlogPost[];
}

export interface IParsedPost extends IBlogPost {
  // parsed_date is a javascript Date object built from published key in
  // IBlogPost
  parsed_date: Date;
  body_css?: React.CSSProperties;
  title_css?: React.CSSProperties;
}

const feedApiURL = "/c2s/feed";
const perUserApiURL = "/c2s/@";

function ParseCSSJson(j?: string) {
  if (j === undefined || j === "") {
    return undefined;
  }
  let p = {};
  try {
    p = JSON.parse(j);
  } catch (err) {
    // Invalid JSON.
    return undefined;
  }
  // TODO(CianLR): Check if p is actually an instace of React.CSSProperties.
  return p as React.CSSProperties;
}

export function ParsePosts(b: IBlogPost[], bodyCssJson?: string, titleCssJson?: string) {
  const bodyCss = ParseCSSJson(bodyCssJson);
  const titleCss = ParseCSSJson(titleCssJson);
  // convert published string to js datetime obj
  b = b as IParsedPost[];
  b.map((e: IParsedPost) => {
    e.parsed_date = new Date(e.published);
    e.body_css = bodyCss;
    e.title_css = titleCss;
    if (e.bio === undefined || e.bio === "") {
      e.bio = "Nowadays everybody wanna talk like they got something to say. \
      But nothing comes out when they move their lips; just a bunch of gibberish.";
    }
    return e;
  });
  return b as IParsedPost[];
}

export function SortPosts(b: IFeedResponse) {
  const p: IParsedPost[] = ParsePosts(b.results, b.post_body_css, b.post_title_css);
  p.sort((n: IParsedPost, m: IParsedPost) => {
    return m.parsed_date.getTime() - n.parsed_date.getTime();
  });
  return p;
}

export function PostsAPIPromise(url: string) {
  return new Promise<IParsedPost[]>((resolve, reject) => {
    superagent
      .get(url)
      .set("Accept", "application/json")
      .end((error, res) => {
        if (error) {
          reject(error);
          return;
        }
        // Feed will respond with an empty response if no blogs are avaiable.
        let posts = res!.body;
        if (posts === null) {
          posts = {results: []};
        }
        const parsedPosts = SortPosts(posts);
        resolve(parsedPosts);
      });
  });
}

export function GetUsersPosts(username: string) {
  const url = `${perUserApiURL}${encodeURIComponent(username)}`;
  return PostsAPIPromise(url);
}

export function GetSinglePost(username: string, id: string) {
  const url = `${perUserApiURL}${encodeURIComponent(username)}/${id}`;
  return PostsAPIPromise(url);
}

export function GetPublicPosts(username= "") {
  const url = username === "" ? feedApiURL : `${feedApiURL}/${encodeURIComponent(username)}`;
  return PostsAPIPromise(url);
}
