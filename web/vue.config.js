module.exports = {
  devServer: {
    client: {
      overlay: {
        warnings: false,
        errors: false
      }
    },
    allowedHosts: [
      'lncmig.local',
      'magnetdb-dev.local',
    ]
  }
}
