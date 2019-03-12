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

interface ISharedPost extends IBlogPost {
  share_datetime: string;
  sharer: string;
  sharer_bio: string;
}

export interface IFeedResponse {
  post_body_css: string;
  post_title_css: string;
  results: IBlogPost[];
  share_results: ISharedPost[];
}

export interface IParsedPost extends IBlogPost {
  // parsed_date is a javascript Date object built from published key in
  // IBlogPost
  parsed_date: Date;
  body_css?: React.CSSProperties;
  title_css?: React.CSSProperties;
}

export interface IParsedSharedPost extends IParsedPost, ISharedPost {
  parsed_share_date: Date;
}

export type IAnyParsedPost = IParsedPost | IParsedSharedPost;

const feedApiURL = "/c2s/feed";
const perUserApiURL = "/c2s/@";

export function IsSharedPost(p: IAnyParsedPost) {
  return (p as IParsedSharedPost).parsed_share_date !== undefined;
}

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

export function ParseSharedPosts(b: ISharedPost[], bodyCssJson?: string, titleCssJson?: string) {
  const bodyCss = ParseCSSJson(bodyCssJson);
  const titleCss = ParseCSSJson(titleCssJson);
  // convert published string to js datetime obj
  b = b as IParsedSharedPost[];
  b.map((e: IParsedSharedPost) => {
    e.parsed_date = new Date(e.published);
    e.parsed_share_date = new Date(e.share_datetime);
    e.body_css = bodyCss;
    e.title_css = titleCss;
    if (e.bio === undefined || e.bio === "") {
      e.bio = "Nowadays everybody wanna talk like they got something to say. \
      But nothing comes out when they move their lips; just a bunch of gibberish.";
    }
    return e;
  });
  return b as IParsedSharedPost[];
}

export function SortPosts(b: IFeedResponse) {
  const p: IParsedPost[] = ParsePosts(b.results, b.post_body_css, b.post_title_css);
  const s: IParsedSharedPost[] = ParseSharedPosts(b.share_results, b.post_body_css, b.post_title_css);

  const l: IAnyParsedPost[] = p.concat(s);

  l.sort((n, m) => {
    const t = (m as IParsedSharedPost).parsed_share_date || m.parsed_date;
    const f = (n as IParsedSharedPost).parsed_share_date || n.parsed_date;
    return t.getTime() - f.getTime();
  });

  return l;
}

export function PostsAPIPromise(url: string) {
  return new Promise<IAnyParsedPost[]>((resolve, reject) => {
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
          posts = {
            results: [],
          };
        }

        if (posts.results === null || posts.results === undefined) {
          posts.results = [];
        }
        if (posts.share_results === null || posts.share_results === undefined) {
          posts.share_results = [];
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
