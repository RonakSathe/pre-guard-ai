export type SiteDecision = "trusted" | "untrusted"

const STORAGE_KEY = "preGuardSiteTrust"

type SiteTrustStore = {
  trusted: string[]
  untrusted: string[]
}

async function getStore(): Promise<SiteTrustStore> {
  const result = await chrome.storage.local.get(STORAGE_KEY)

  return (
    result[STORAGE_KEY] || {
      trusted: [],
      untrusted: []
    }
  )
}

function normalizeHostname(hostname: string): string {
  return hostname.toLowerCase().replace(/^www\./, "")
}

export function getHostname(url: string): string | null {
  try {
    const parsed = new URL(url)

    if (
      parsed.protocol !== "http:" &&
      parsed.protocol !== "https:"
    ) {
      return null
    }

    return normalizeHostname(parsed.hostname)
  } catch {
    return null
  }
}

export async function getSiteDecision(
  url: string
): Promise<SiteDecision | null> {
  const hostname = getHostname(url)

  if (!hostname) {
    return null
  }

  const store = await getStore()

  if (store.trusted.includes(hostname)) {
    return "trusted"
  }

  if (store.untrusted.includes(hostname)) {
    return "untrusted"
  }

  return null
}

export async function rememberSite(
  url: string,
  decision: SiteDecision
): Promise<void> {
  const hostname = getHostname(url)

  if (!hostname) {
    throw new Error("Invalid HTTP/HTTPS URL")
  }

  const store = await getStore()

  store.trusted = store.trusted.filter(
    (site) => site !== hostname
  )

  store.untrusted = store.untrusted.filter(
    (site) => site !== hostname
  )

  store[decision].push(hostname)

  await chrome.storage.local.set({
    [STORAGE_KEY]: store
  })
}