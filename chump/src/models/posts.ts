import * as Promise from "bluebird";
import * as superagent from "superagent";

interface IBlogPost {
  author: string;
  author_display: string;
  author_host: string;
  author_id: number;
  bio: string;
  body: string;
  global_id: number;
  image: string;
  likes_count: number;
  md_body: string;
  is_liked: boolean;
  published: string;
  title: string;
  is_followed: boolean;
  is_shared: boolean;
  shares_count: number;
  tags: string[];
  summary: string;
}

interface ISharedPost extends IBlogPost {
  share_datetime: string;
  sharer: string;
  sharer_bio: string;
  sharer_host: string;
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
}

export interface IParsedSharedPost extends IParsedPost, ISharedPost {
  parsed_share_date: Date;
}

export type IAnyParsedPost = IParsedPost | IParsedSharedPost;

const feedApiURL = "/c2s/feed";
const singleArticleApiURL = "/c2s/article/";
const perUserApiURL = "/c2s/@";

// CleanParsedPost ensures that fields not encoded by the frontend get
// correct default values.
//
// This function modifies the post in place, because of typescript weirdness
// when you're using returning alias types.
export function CleanParsedPost(p: IAnyParsedPost) {
  if (typeof(p.author_display) === "undefined" || p.author_display === "") {
    p.author_display = p.author;
  }
  if (typeof(p.likes_count) === "undefined") {
    p.likes_count = 0;
  }
  if (typeof(p.author_host) === "undefined") {
    p.author_host = "";
  }
  if (typeof(p.is_liked) === "undefined") {
    p.is_liked = false;
  }
  if (typeof(p.shares_count) === "undefined") {
    p.shares_count = 0;
  }
  if (typeof(p.is_shared) === "undefined") {
    p.is_shared = false;
  }
  if (typeof(p.bio) === "undefined" || p.bio === "") {
    p.bio = "Nowadays everybody wanna talk like they got something to say. \
    But nothing comes out when they move their lips; just a bunch of gibberish.";
  }
}

export function IsSharedPost(p: IAnyParsedPost) {
  return (p as IParsedSharedPost).parsed_share_date !== undefined;
}

export function ParsePosts(b: IBlogPost[], bodyCssJson?: string, titleCssJson?: string) {
  // convert published string to js datetime obj
  b = b as IParsedPost[];
  b.map((e: IParsedPost) => {
    e.parsed_date = new Date(e.published);
    CleanParsedPost(e);
    return e;
  });
  return b as IParsedPost[];
}

export function ParseSharedPosts(b: ISharedPost[], bodyCssJson?: string, titleCssJson?: string) {
  b = b as IParsedSharedPost[];
  b.map((e: IParsedSharedPost) => {
    e.parsed_date = new Date(e.published);
    e.parsed_share_date = new Date(e.share_datetime);
    CleanParsedPost(e);
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
  const url = `${perUserApiURL}${username}`;
  return PostsAPIPromise(url);
}

export function GetSinglePost(id: string) {
  const url = `${singleArticleApiURL}${id}`;
  return PostsAPIPromise(url);
}

export function GetPublicPosts(userId= 0) {
  const url = userId === 0 ? feedApiURL : `${feedApiURL}/${userId.toString()}`;
  return PostsAPIPromise(url);
}
