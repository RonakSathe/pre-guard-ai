import {
  getHostname,
  getSiteDecision,
  rememberSite
} from "./siteTrust"

async function testSiteTrust() {
  const testUrl = "https://www.example.com/test/page"

  console.log("=== PRE-GUARD SITE TRUST TEST ===")

  console.log(
    "Hostname:",
    getHostname(testUrl)
  )

  console.log(
    "Before decision:",
    await getSiteDecision(testUrl)
  )

  await rememberSite(testUrl, "trusted")

  console.log(
    "After trusted:",
    await getSiteDecision(testUrl)
  )

  await rememberSite(testUrl, "untrusted")

  console.log(
    "After untrusted:",
    await getSiteDecision(testUrl)
  )

  console.log("=== TEST COMPLETE ===")
}

testSiteTrust()