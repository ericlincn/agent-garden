import { spawn } from "child_process"
import path from "path"

const SOUND_SCRIPT = path.resolve(process.cwd(), ".bin/play-sound.py")

let alertDebounce = false

export const SoundBridge = async () => {
  const play = (soundType: "alert" | "idle") => {
    spawn("python", [SOUND_SCRIPT, soundType], {
      stdio: ["ignore", "ignore", "ignore"],
    }).unref()
  }

  return {
    event: async ({ event }) => {
      if (event.type === "permission.asked") {
        if (alertDebounce) return
        alertDebounce = true
        play("alert")
      }
      if (event.type === "permission.replied") {
        alertDebounce = false
      }
      if (event.type === "session.idle") {
        alertDebounce = false
        play("idle")
      }
    },
  }
}
