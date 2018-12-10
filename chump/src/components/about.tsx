import * as React from "react";
import { Link } from "react-router-dom";

export const About: React.StatelessComponent<{}> = () => {
  return (
    <div>
      <div className="pure-u-5-24"/>
      <div className="pure-u-10-24">
        <h4>Welcome to Rabble!</h4>
        <p>Rabble is a new federated blogging platform that aims to be easy to use, trustworthy, and lightweight.</p>

        <h4>Be part of the federation.</h4>
        <p>This is just one instance in a network of connected servers. You can choose to register on whichever Rabble
        server you like, and you'll be able to follow and interact with authors on other Rabble servers on the network.
        You are free to choose a server based on what's important to you; be it community rules, uptime, language,
        interface, or anything else.</p>
        <p>Behind the scenes, Rabble uses the <a href="https://activitypub.rocks">ActivityPub protocol</a> to achieve
        this federation.</p>

        <h4>Go beyond Rabble.</h4>
        <p>You can use Rabble to follow your favourite RSS feeds, and you can follow a Rabble blog from your own RSS
        reader as well. Rabble will also eventually support interacting with other ActivityPub-compliant services,
        like <a href="https://joinmastodon.org">Mastodon</a>, <a href="https://joinpeertube.org">PeerTube</a>, and&nbsp;
        <a href="https://plume-org.github.io/Plume/">Plume</a>.</p>

        <h4>Interested?</h4>
        <p>If you're interested in trying out Rabble, hit the <Link to="/register">Register</Link> button above to
        sign up to this server!</p>

        <div className="pure-u-1-8" />
        <img src="https://i.imgur.com/Kzi4Jdy.jpg" className="pure-u-3-4" style={{marginBottom: 0}} />
        <p style={{textAlign: "center", fontStyle: "italic", marginTop: 0}}>The Rabble team</p>
        <p>Rabble was developed at Dublin City University by Aaron Delaney, Noah Ó Donnaile, Ross O'Sullivan, and Cian
        Ruane, under the supervision of Dr. Jennifer Foster and Dr. Andrew McCarren.</p>
      </div>
    </div>
  );
};
