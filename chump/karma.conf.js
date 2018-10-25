// Karma configuration
// Generated on Sat Oct 20 2018 15:51:56 GMT+0100 (Irish Standard Time)

var webpackConfig = require("./webpack.config");

module.exports = function(config) {
  config.set({
    // base path that will be used to resolve all patterns (eg. files, exclude)
    basePath: '',

    // frameworks to use
    frameworks: ['mocha', 'chai', 'sinon'],

    // list of files / patterns to load in the browser
    files: [
      'node_modules/@babel/polyfill/dist/polyfill.js',
      'test/**/*.ts',
      'test/**/*.tsx',
    ],

    // list of files / patterns to exclude
    exclude: [],

    // preprocess matching files before serving them to the browser
    preprocessors: {
      'test/**/*.tsx': ["webpack"],
      'test/**/*.ts': ["webpack"],
    },

    webpack: {
      stats: 'errors-only',
      mode: 'development',
      devtool: 'inline-source-map',
      module: webpackConfig.module,
      resolve: webpackConfig.resolve
    },

    // test results reporter to use
    reporters: ['mocha'],

    // web server port
    port: 9876,

    // enable / disable colors in the output (reporters and logs)
    colors: true,

    // level of logging
    // possible values: config.LOG_DISABLE || config.LOG_ERROR || config.LOG_WARN || config.LOG_INFO || config.LOG_DEBUG
    logLevel: config.LOG_INFO,

    // start these browsers
    browsers: ['RabbleChromium'],

    customLaunchers: {
      RabbleChromium: {
        base: 'ChromiumHeadless',
        flags: ["--no-sandbox"]
      }
    },

    singleRun: true,

    // Concurrency level
    // how many browser should be started simultaneous
    concurrency: Infinity
  })
}
