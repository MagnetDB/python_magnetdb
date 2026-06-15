class QueueRunner {
  constructor() {
    this.queue = []
    this.locked = false
  }

  run(cb) {
    const alreadyLocked = this.locked
    return new Promise((resolve, reject) => {
      this.locked = true
      this.queue.push([cb, resolve, reject])
      if (!alreadyLocked) {
        setTimeout(async () => {
          while (this.queue.length) {
            const [cb, resolve, reject] = this.queue.shift()
            try {
              resolve(await cb())
            } catch (e) {
              reject(e)
            }
          }
          this.locked = false
        })
      }
    })
  }
}

export default QueueRunner
