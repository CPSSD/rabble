import * as Promise from 'bluebird';
import { expect } from "chai";

import { IBlogPost, GetPublicPosts } from "../src/api/posts"

describe("GetPublicPosts", () => {

  it("mocks post data", (done) => {
    GetPublicPosts().then((posts: IBlogPost[]) => {
      expect(posts).to.have.lengthOf(4);
      done();
    });
  })

})
