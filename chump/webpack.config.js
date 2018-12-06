const HtmlWebpackPlugin = require("html-webpack-plugin");

// Based on code in typescript documentation, licensed under Apache License 2.0
// See https://git.io/fxCgz for a link to the documentation.
module.exports = {
    entry: "./src/index.tsx",
    output: {
        filename: "bundle.js",
        path: __dirname + "/dist",
        publicPath: "/assets/",
        chunkFilename: "[id].[chunkhash].js"
    },

    // Enable sourcemaps for debugging webpack's output.
    devtool: "source-map",

    resolve: {
        // Add '.ts' and '.tsx' as resolvable extensions.
        extensions: [".ts", ".tsx", ".js", ".json"]
    },

    module: {
        rules: [
            // All files with a '.ts' or '.tsx' extension will be handled by
            // 'awesome-typescript-loader'.
            { test: /\.tsx?$/, loader: "awesome-typescript-loader" },

            { test: /\.css$/, use: ["style-loader", "css-loader"] },

            // All output '.js' files will have any sourcemaps re-processed by 'source-map-loader'.
            { enforce: "pre", test: /\.js$/, loader: "source-map-loader" }
        ]
    },

    // When importing a module whose path matches one of the following, just
    // assume a corresponding global variable exists and use that instead.
    // This is important because it allows us to avoid bundling all of our
    // dependencies, which allows browsers to cache those libraries between builds.
    // These also must be defined in the plugins field, to keep them in the
    // generated index.html.
    externals: {
        "react": "React",
        "react-dom": "ReactDOM"
    },

    plugins: [
        new HtmlWebpackPlugin({
            title: "Rabble",
            inject: false,
            template: require("html-webpack-template"),
            appMountId: "root",
            // Provide cachable browser links to well known dependencies.
            // This keeps the bundle size and loading speed down.
            links: [
                "https://unpkg.com/purecss@1.0.0/build/pure-min.css",
                "https://fonts.googleapis.com/css?family=Lato",
            ],
            scripts: [
                "https://unpkg.com/react@16/umd/react.development.js",
                "https://unpkg.com/react-dom@16/umd/react-dom.development.js",
            ]
        })
    ]
}
