import * as Promise from 'bluebird';

export interface IBlogPost {
  author: string;
  title: string;
  blogText: string;
}

export function GetPublicPosts() {
  let blogs: IBlogPost[] = [
    {
      author: "Aaron",
      title: "Welcome to Rabble",
      blogText: "Your blog could be here!",
    },
    {
      author: "Cian",
      title: "Databases",
      blogText: "they're <i>cool</i>, trust me.\n<b>TRUST ME.</b>",
    },
    {
      author: "Noah",
      title: "Gaeilge",
      blogText: "Ní maith liom an scoil ach is maith liom toast na Fraince.",
    },
    {
      author: "Ross",
      title: "Bird People",
      blogText: "Love 'em or hate 'em, bird people are here to stay.",
    },
  ];

  return new Promise<IBlogPost[]>(resolve => {
    resolve(blogs);
  });
}
