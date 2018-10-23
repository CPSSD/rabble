import * as Promise from 'bluebird';

export interface IBlogPost {
  author: string;
  title: string;
  body: string;
}

export function GetPublicPosts() {
  let blogs: IBlogPost[] = [
    {
      author: "Aaron",
      title: "Welcome to Rabble",
      body: "Your blog could be here!",
    },
    {
      author: "Cian",
      title: "Databases",
      body: "they're <i>cool</i>, trust me.\n<b>TRUST ME.</b>",
    },
    {
      author: "Noah",
      title: "Gaeilge",
      body: "Ní maith liom an scoil ach is maith liom toast na Fraince.",
    },
    {
      author: "Ross",
      title: "Bird People",
      body: "Love 'em or hate 'em, bird people are here to stay.",
    },
  ];

  return new Promise<IBlogPost[]>(resolve => {
    resolve(blogs);
  });
}
