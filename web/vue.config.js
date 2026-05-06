module.exports = {
  devServer: {
    allowedHosts: [
      'lncmig.local',
      'magnetdb-dev.local',
    ],
    client: {
      webSocketURL: 'auto://0.0.0.0:0/ws',
    },
  },
  configureWebpack: {
    resolve: {
      fallback: {
        stream: false,
        assert: false,
      },
    },
  },
}
