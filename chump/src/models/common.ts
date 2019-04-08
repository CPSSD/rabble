import * as request from "superagent";

// PartialResponse is a partial response from a request. This allows us to
// create a subset of responses while testing models, whilst still allowing
// type checking.
//
// This type checking doesn't extend to the resolve function when dealing
// with Promises, so one still needs to be a little careful.
export type PartialResponse = Partial<request.Response>;
