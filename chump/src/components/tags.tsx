import * as React from 'react'

import { RootComponent } from "./root_component";

interface ITagProps {
  tags: string[];
  tagHolderClass: string;
  tagClass: string;
}

export class Tags extends RootComponent<ITagProps, {}> {
  constructor(props: ITagProps) {
    super(props);
  }

  public render() {
    return this.props.tags.map((e: string, i: number) => {
        return (
          <div className={this.props.tagHolderClass} key={i}>
            <p className={this.props.tagClass}>{e}</p>
          </div>
        );
    });
  }
}
