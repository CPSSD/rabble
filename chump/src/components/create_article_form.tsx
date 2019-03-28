import * as React from "react";
import * as RModal from "react-modal";
import { HashRouter } from "react-router-dom";
import * as TagsInput from "react-tagsinput";
import * as config from "../../rabble_config.json";
import { CreatePreview } from "../models/article";
import { IParsedPost } from "../models/posts";
import { Post } from "./post";
import { RootComponent } from "./root_component";

interface IFormState {
  blogText: string;
  post: IParsedPost;
  showModal: boolean;
  tags: string[];
  title: string;
}

interface IFormProps {
  username: string;
  prefillState: (updateFunc: (a: string, b: string, c: string[]) => void) => void;
  onSubmit: (u: string, t: string, b: string, tags: string[]) => any;
}

const defaultBio = "Nowadays everybody wanna talk like they got something to say. \
But nothing comes out when they move their lips; just a bunch of gibberish.";
const defaultImage = "https://qph.fs.quoracdn.net/main-qimg-8aff684700be1b8c47fa370b6ad9ca13.webp";
const EMPTY_TITLE_ERROR = "A post cannot have an empty title";

export class CreateArticleForm extends RootComponent<IFormProps, IFormState> {
  constructor(props: IFormProps) {
    super(props);

    this.state = {
      blogText: "",
      post: {
        author: "string",
        author_display: "",
        author_host: "",
        author_id: 0,
        bio: defaultBio,
        body: "string",
        global_id: 3,
        image: defaultImage,
        is_followed: false,
        is_liked: false,
        is_shared: false,
        likes_count: 0,
        md_body: "",
        parsed_date: new Date(),
        published: "",
        shares_count: 0,
        tags: [],
        title: "string",
      },
      showModal: false,
      tags: [],
      title: "",
    };

    this.handleTitleInputChange = this.handleTitleInputChange.bind(this);
    this.handleTagInputChange = this.handleTagInputChange.bind(this);
    this.handleTextAreaChange = this.handleTextAreaChange.bind(this);
    this.handleSubmitForm = this.handleSubmitForm.bind(this);
    this.handlePreview = this.handlePreview.bind(this);
    this.handleClosePreview = this.handleClosePreview.bind(this);
    this.renderModal = this.renderModal.bind(this);
  }

  public componentDidMount() {
    this.props.prefillState((title: string, blogText: string, tags: string[]) => {
      this.setState({ title, blogText, tags });
    });
  }

  public renderModal() {
    return (
      <div>
        <RModal
           isOpen={this.state.showModal}
           ariaHideApp={false}
        >
          <div className="pure-g topnav">
            <div className="pure-u-10-24">
              <button
                className="pure-button pure-input-1-3 pure-button-primary primary-button"
                onClick={this.handleClosePreview}
              >
                {config.close_preview}
              </button>
            </div>
            <div className="pure-u-10-24"/>
            <div className="pure-u-4-24">
              <button
                className="pure-button pure-input-1-3 pure-button-primary primary-button preview-post"
                onClick={this.handleSubmitForm}
              >
                Post
              </button>
            </div>
          </div>
          <div className="pure-g" key={1}>
            <HashRouter>
              <Post username={this.props.username} blogPost={this.state.post} preview={true} customCss={true}/>
            </HashRouter>
          </div>
        </RModal>
      </div>
    );
  }

  public render() {
    const previewModel = this.renderModal();
    return (
      <div>
        <form
          className="pure-form pure-form-aligned"
          onSubmit={this.handleSubmitForm}
          id="create_post_form"
        >
          <div className="pure-control-group">
            <input
              type="text"
              name="title"
              value={this.state.title}
              onChange={this.handleTitleInputChange}
              className="pure-input-1-2"
              placeholder={config.title_text}
              required={true}
            />
            <TagsInput
              value={this.state.tags}
              onChange={this.handleTagInputChange}
              onlyUnique={true}
              maxTags={7}
            />
            <textarea
              name="blogText"
              value={this.state.blogText}
              onChange={this.handleTextAreaChange}
              className="pure-input-1 blog-input"
              placeholder={config.start_here}
              rows={config.write_box_rows}
            />
          </div>
        </form>
        <div className="pure-button-group" role="group">
          <button
            onClick={this.handlePreview}
            className="pure-button pure-input-1-3 pure-button-primary primary-button"
          >
            {config.preview}
          </button>
          <button
            type="submit"
            className="pure-button pure-input-1-3 pure-button-primary primary-button"
            form="create_post_form"
          >
            {config.post}
          </button>
        </div>
        {previewModel}
      </div>
    );
  }

  private handleTitleInputChange(event: React.ChangeEvent<HTMLInputElement>) {
    const target = event.target;
    this.setState({
      title: target.value,
    });
  }

  private handleTagInputChange(tags: string[]) {
    const uniqueTags = [...new Set(tags)];
    this.setState({
      tags: uniqueTags,
    });
  }

  private handleTextAreaChange(event: React.ChangeEvent<HTMLTextAreaElement>) {
    const target = event.target;
    this.setState({
      blogText: target.value,
    });
  }

  private handleClosePreview() {
    this.setState({ showModal: false });
  }

  private handlePreview(event: React.MouseEvent<HTMLButtonElement>) {
    event.preventDefault();
    const promise = CreatePreview(this.state.title, this.state.blogText);
    promise
      .then((res: any) => {
        const post = res!.body;
        if (post === null) {
          this.alertUser("Could not preview");
          return;
        }
        post.parsed_date = new Date();
        post.bio = defaultBio;
        post.likes_count = 0;
        post.shares_count = 0;
        post.image = defaultImage;
        this.setState({
          post,
          showModal: true,
        });
      })
      .catch((err: any) => {
        let message = err.message;
        if (err.response) {
          message = err.response.text;
        }
        this.alertUser(message);
      });
  }

  private handleSubmitForm(event: React.FormEvent<HTMLFormElement> | React.MouseEvent<HTMLButtonElement>) {
    event.preventDefault();
    if (this.state.title === "") {
      this.alertUser(EMPTY_TITLE_ERROR);
      return;
    }

    // if posted from modal, need to close modal after post
    let showModal = this.state.showModal;
    if (event.type === "click" || event.nativeEvent instanceof MouseEvent) {
      showModal = false;
    }
    this.props.onSubmit(this.state.title, this.state.blogText, this.state.tags)
      .then((res: any) => {
        let message = "Posted article";
        if (res.text) {
          message = res.text;
        }
        this.alertUser(message);
        this.setState({
          blogText: "",
          showModal,
          title: "",
        });
      })
      .catch((err: any) => {
        let message = err.message;
        if (err.response) {
          message = err.response.text;
        }
        this.alertUser(message);
      });
  }
}
