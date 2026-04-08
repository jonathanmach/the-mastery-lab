import { ref, computed, watch } from 'vue'

export const CHARSETS = [
  { id: 'digits',   label: 'Digits only (0–9)',                        size: 10 },
  { id: 'lower',    label: 'Lowercase alpha (a–z)',                     size: 26 },
  { id: 'alnum_ci', label: 'Alphanumeric, case-insensitive (0–9, a–z)', size: 36 },
  { id: 'alnum_cs', label: 'Alphanumeric, case-sensitive (0–9, a–Z)',   size: 62 },
  { id: 'full',     label: 'Alphanumeric + symbols (printable ASCII)',  size: 94 },
]

export const ATTACKER_PROFILES = [
  { id: 'script_kiddie',   label: 'Script Kiddie',   parallelIps: 10 },
  { id: 'organized_crime', label: 'Organized Crime', parallelIps: 1_000 },
  { id: 'nation_state',    label: 'Nation-State',    parallelIps: 1_000_000 },
]

const COSMIC_DAYS = {
  universe_x1000: 13.8e9 * 365.25 * 1000,
  universe:       13.8e9 * 365.25,
  earth:          4.54e9 * 365.25,
  million_years:  1_000_000 * 365.25,
  civilization:   10_000 * 365.25,
  century:        100 * 365.25,
  decade:         10 * 365.25,
  year:           365.25,
  month:          30,
}

export function useEntropy() {
  // ── Inputs ──────────────────────────────────────────────────────────────────
  const charsetId         = ref('alnum_ci')
  const tokenLength       = ref(6)
  const additionalEntropy = ref(1200)
  const numberOfSecrets   = ref(500)
  const rateLimitingEnabled = ref(true)
  const rawAttemptsPerDay   = ref(1_000_000_000)   // 1 billion/day ≈ 11,574/sec (unthrottled online)
  const perIpPerDay         = ref(20)
  const perUserPerDay       = ref(10)
  const perDevicePerDay     = ref(20)
  const parallelIps         = ref(100)
  const attackerProfileId   = ref('organized_crime')

  // ── Charset size ─────────────────────────────────────────────────────────────
  const charsetSize = computed(() =>
    CHARSETS.find(c => c.id === charsetId.value)?.size ?? 62
  )

  // ── Keyspace (BigInt) ────────────────────────────────────────────────────────
  const keyspaceBigInt = computed(() => {
    const len  = Math.max(0, Math.min(256, Math.floor(tokenLength.value)))
    const cs   = BigInt(charsetSize.value)
    const mult = BigInt(Math.max(1, Math.floor(additionalEntropy.value)))
    if (len === 0) return mult
    return cs ** BigInt(len) * mult
  })

  // ── Entropy bits (float) ─────────────────────────────────────────────────────
  const entropyBits = computed(() => {
    const len   = Math.max(0, tokenLength.value)
    const extra = Math.max(1, additionalEntropy.value)
    return len * Math.log2(charsetSize.value) + Math.log2(extra)
  })

  // ── Rate limiting ────────────────────────────────────────────────────────────
  // Per-IP and per-device limits scale with the number of parallel IPs/fingerprints
  // the attacker controls (both can be rotated/spoofed).
  // Per-user is an absolute ceiling on attempts against one account — it cannot
  // be bypassed by using more IPs. It is the dominant protection in most real systems.
  const effectivePerIpLimit = computed(() =>
    Math.max(0, Math.min(perIpPerDay.value, perDevicePerDay.value))
  )

  const totalAttemptsPerDay = computed(() => {
    if (!rateLimitingEnabled.value) return Math.max(0, rawAttemptsPerDay.value)
    const ipRate   = effectivePerIpLimit.value * parallelIps.value
    const userRate = perUserPerDay.value * Math.max(1, Math.floor(numberOfSecrets.value))
    return Math.min(ipRate, userRate)
  })

  // ── Time to crack ────────────────────────────────────────────────────────────
  // For M valid secrets in a keyspace of K, sampling without replacement:
  //   E[guesses to first hit] = (K + 1) / (M + 1)
  // Special case M=1: (K+1)/2 ≈ K/2 — the classic "half the keyspace" result.
  const daysToCrack = computed(() => {
    const rate = totalAttemptsPerDay.value
    if (rate <= 0) return Infinity

    const M  = Math.max(1, Math.floor(numberOfSecrets.value))
    const ks = keyspaceBigInt.value

    if (ks > BigInt(Number.MAX_SAFE_INTEGER)) {
      const numerator = ks + 1n
      const denominator = BigInt(M + 1) * BigInt(Math.floor(rate))
      if (denominator === 0n) return Infinity
      const days = numerator / denominator
      return days > BigInt(Number.MAX_SAFE_INTEGER) ? Number.MAX_SAFE_INTEGER : Number(days)
    }
    return (Number(ks) + 1) / ((M + 1) * rate)
  })

  const yearsToCrack = computed(() => daysToCrack.value / 365.25)

  // ── Security tier ────────────────────────────────────────────────────────────
  const securityTier = computed(() => {
    const y = yearsToCrack.value
    if (y > 100) return 'green'
    if (y >= 10) return 'amber'
    return 'red'
  })

  // ── NIST compliance ──────────────────────────────────────────────────────────
  const meetsNist = computed(() => entropyBits.value >= 112)

  // ── Cosmic context ───────────────────────────────────────────────────────────
  const cosmicContext = computed(() => {
    const d = daysToCrack.value
    if (!isFinite(d) || d >= Number.MAX_SAFE_INTEGER) return 'Beyond the heat death of the universe'
    if (d > COSMIC_DAYS.universe_x1000) return 'Longer than 1,000× the age of the universe'
    if (d > COSMIC_DAYS.universe)       return 'Longer than the age of the universe (13.8 billion years)'
    if (d > COSMIC_DAYS.earth)          return 'Longer than the age of the Earth (4.5 billion years)'
    if (d > COSMIC_DAYS.million_years)  return 'Longer than 1 million years'
    if (d > COSMIC_DAYS.civilization)   return 'Longer than human civilization (10,000 years)'
    if (d > COSMIC_DAYS.century)        return 'More than a century'
    if (d > COSMIC_DAYS.decade)         return 'More than a decade'
    if (d > COSMIC_DAYS.year)           return 'More than a year'
    if (d > COSMIC_DAYS.month)          return 'More than a month'
    return 'Less than a month — critically vulnerable'
  })

  // ── Attacker profile sync ────────────────────────────────────────────────────
  function setAttackerProfile(profileId) {
    const profile = ATTACKER_PROFILES.find(p => p.id === profileId)
    if (!profile) return
    attackerProfileId.value = profileId
    parallelIps.value = profile.parallelIps
  }

  watch(parallelIps, (val) => {
    const match = ATTACKER_PROFILES.find(p => p.parallelIps === val)
    attackerProfileId.value = match ? match.id : null
  })

  // ── URL serialisation ────────────────────────────────────────────────────────
  function toQueryParams() {
    return new URLSearchParams({
      cs:  charsetId.value,
      len: tokenLength.value,
      ae:  additionalEntropy.value,
      m:   numberOfSecrets.value,
      rl:  rateLimitingEnabled.value ? '1' : '0',
      raw: rawAttemptsPerDay.value,
      ip:  perIpPerDay.value,
      up:  perUserPerDay.value,
      dp:  perDevicePerDay.value,
      pip: parallelIps.value,
    }).toString()
  }

  function fromQueryParams(search) {
    const p = new URLSearchParams(search)
    const validCharset = id => CHARSETS.some(c => c.id === id)
    if (p.has('cs')  && validCharset(p.get('cs')))       charsetId.value         = p.get('cs')
    if (p.has('len') && !isNaN(+p.get('len')))           tokenLength.value       = Math.min(256, Math.max(1, +p.get('len')))
    if (p.has('ae')  && !isNaN(+p.get('ae')))            additionalEntropy.value = Math.max(1, +p.get('ae'))
    if (p.has('m')   && !isNaN(+p.get('m')))             numberOfSecrets.value     = Math.max(1, Math.floor(+p.get('m')))
    if (p.has('rl'))                                      rateLimitingEnabled.value = p.get('rl') !== '0'
    if (p.has('raw') && !isNaN(+p.get('raw')))            rawAttemptsPerDay.value   = Math.max(1, +p.get('raw'))
    if (p.has('ip')  && !isNaN(+p.get('ip')))            perIpPerDay.value       = Math.max(0, +p.get('ip'))
    if (p.has('up')  && !isNaN(+p.get('up')))            perUserPerDay.value     = Math.max(0, +p.get('up'))
    if (p.has('dp')  && !isNaN(+p.get('dp')))            perDevicePerDay.value   = Math.max(0, +p.get('dp'))
    if (p.has('pip') && !isNaN(+p.get('pip')))           parallelIps.value       = Math.max(1, +p.get('pip'))
  }

  return {
    // Refs
    charsetId, tokenLength, additionalEntropy, numberOfSecrets,
    rateLimitingEnabled, rawAttemptsPerDay,
    perIpPerDay, perUserPerDay, perDevicePerDay,
    parallelIps, attackerProfileId,
    // Constants
    CHARSETS, ATTACKER_PROFILES,
    // Computed
    charsetSize, keyspaceBigInt, entropyBits,
    effectivePerIpLimit, totalAttemptsPerDay,
    daysToCrack, yearsToCrack,
    securityTier, meetsNist, cosmicContext,
    // Methods
    setAttackerProfile, toQueryParams, fromQueryParams,
  }
}
