/**
 * Format a large number to a human-readable string with named magnitudes.
 * @param {number|BigInt} n
 * @returns {string}
 */
export function formatLargeNumber(n) {
  const num = typeof n === 'bigint' ? Number(n) : n
  if (!isFinite(num)) return '∞'
  if (num < 1_000)         return num.toLocaleString('en-US', { maximumFractionDigits: 2 })
  if (num < 1_000_000)     return `${(num / 1_000).toFixed(2)} thousand`
  if (num < 1e9)           return `${(num / 1_000_000).toFixed(2)} million`
  if (num < 1e12)          return `${(num / 1e9).toFixed(2)} billion`
  if (num < 1e15)          return `${(num / 1e12).toFixed(2)} trillion`
  if (num < 1e18)          return `${(num / 1e15).toFixed(2)} quadrillion`
  if (num < 1e21)          return `${(num / 1e18).toFixed(2)} quintillion`
  if (num < 1e24)          return `${(num / 1e21).toFixed(2)} sextillion`
  return num.toExponential(2)
}

/**
 * Format a duration in days to the most meaningful human-readable unit.
 * @param {number} days
 * @returns {string}
 */
export function formatDuration(days) {
  if (!isFinite(days) || days >= Number.MAX_SAFE_INTEGER) return '∞ (effectively forever)'
  if (days < 1/24)    return `${(days * 24 * 60).toFixed(1)} minutes`
  if (days < 1)       return `${(days * 24).toFixed(1)} hours`
  if (days < 30)      return `${Math.round(days)} day${Math.round(days) !== 1 ? 's' : ''}`
  if (days < 365.25)  return `~${Math.round(days / 30)} months`
  const years = days / 365.25
  if (years < 10)     return `~${years.toFixed(1)} years`
  if (years < 1_000)  return `~${Math.round(years).toLocaleString('en-US')} years`
  if (years < 1e6)    return `~${(years / 1_000).toFixed(1)}K years`
  if (years < 1e9)    return `~${(years / 1e6).toFixed(2)} million years`
  if (years < 1e12)   return `~${(years / 1e9).toFixed(2)} billion years`
  return `~${years.toExponential(2)} years`
}

/**
 * Format entropy bits to 1 decimal place.
 * @param {number} bits
 * @returns {string}
 */
export function formatBits(bits) {
  if (!isFinite(bits)) return '∞'
  return bits.toFixed(1)
}
