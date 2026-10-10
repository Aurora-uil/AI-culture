export type GameCue = 'paper' | 'confirm' | 'warning' | 'transition'

const SOUND_KEY = 'tongxin.sound'
let audioContext: AudioContext | null = null

export function getSoundEnabled() {
  try {
    return localStorage.getItem(SOUND_KEY) !== 'off'
  } catch {
    return true
  }
}

export function setSoundEnabled(enabled: boolean) {
  try {
    localStorage.setItem(SOUND_KEY, enabled ? 'on' : 'off')
  } catch {
    // 设置保存失败时，当前页面仍可继续使用。
  }
}

export function playGameCue(kind: GameCue, enabled = getSoundEnabled()) {
  if (!enabled || typeof window === 'undefined') return
  try {
    audioContext ??= new AudioContext()
    void audioContext.resume()
    const oscillator = audioContext.createOscillator()
    const gain = audioContext.createGain()
    const now = audioContext.currentTime
    const cue = {
      paper: { from: 178, to: 132, duration: 0.055, volume: 0.018, wave: 'triangle' as OscillatorType },
      confirm: { from: 280, to: 430, duration: 0.12, volume: 0.028, wave: 'sine' as OscillatorType },
      warning: { from: 150, to: 105, duration: 0.16, volume: 0.024, wave: 'sawtooth' as OscillatorType },
      transition: { from: 96, to: 164, duration: 0.22, volume: 0.018, wave: 'triangle' as OscillatorType },
    }[kind]
    oscillator.type = cue.wave
    oscillator.frequency.setValueAtTime(cue.from, now)
    oscillator.frequency.exponentialRampToValueAtTime(cue.to, now + cue.duration)
    gain.gain.setValueAtTime(0.0001, now)
    gain.gain.exponentialRampToValueAtTime(cue.volume, now + 0.018)
    gain.gain.exponentialRampToValueAtTime(0.0001, now + cue.duration)
    oscillator.connect(gain).connect(audioContext.destination)
    oscillator.start(now)
    oscillator.stop(now + cue.duration + 0.01)
  } catch {
    // 浏览器不支持或拒绝音频时保持静默。
  }
}
