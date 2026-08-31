/**
 * Automated browser verification for the Analyze Location flow.
 * Opens the app in a real (headless) Chromium, clicks the Leaflet map,
 * presses Analyze, and reports what happened + all console errors.
 *
 * Run:  node scripts/verify-analyze.mjs
 */
import { chromium } from 'playwright'

const BASE = process.env.BASE_URL || 'http://localhost:5173'

// Use system Edge (no download needed); fall back to bundled Chromium.
let browser
try {
  browser = await chromium.launch({ channel: 'msedge', headless: true })
  console.log('Using Microsoft Edge (system channel)')
} catch {
  browser = await chromium.launch()
  console.log('Using bundled Chromium')
}
const page = await browser.newPage({ viewport: { width: 1400, height: 900 } })

const logs = []
page.on('console', (m) => logs.push(`[console.${m.type()}] ${m.text()}`))
page.on('pageerror', (e) => logs.push(`[PAGEERROR] ${e.message}`))
page.on('requestfailed', (r) => logs.push(`[requestfailed] ${r.url()} — ${r.failure()?.errorText}`))
page.on('response', (r) => {
  if (r.status() >= 400) logs.push(`[http ${r.status()}] ${r.url()}`)
})

console.log('Opening', `${BASE}/analyze`)
await page.goto(`${BASE}/analyze`, { waitUntil: 'domcontentloaded' })
await page.waitForSelector('.leaflet-container', { timeout: 15000 })
await page.waitForTimeout(1500)

const hintBefore = await page.locator('.map-hint').first().innerText()

// Click the middle of the map
const map = page.locator('.leaflet-container').first()
const box = await map.boundingBox()
await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2)
await page.waitForTimeout(1000)
const hintAfter = await page.locator('.map-hint').first().innerText()

// Press Analyze
await page.getByRole('button', { name: /Analyze risk/i }).click()
await page.waitForTimeout(8000)

const pageText = await page.locator('.page').innerText()
await page.screenshot({ path: 'analyze-test.png', fullPage: true })

console.log('──────────────────────────────────────────')
console.log('HINT BEFORE MAP CLICK :', hintBefore.trim())
console.log('HINT AFTER MAP CLICK  :', hintAfter.trim())
console.log('MAP CLICK REGISTERED  :', hintAfter.includes('Selected'))
console.log('RESULT SHOWN          :', pageText.includes('Landslide Risk Score'))
console.log('PLACEHOLDER STILL     :', pageText.includes('Select a location and press Analyze'))
console.log('ERROR SHOWN           :', pageText.includes('Pehle upar map par click'))
console.log('──────────────────────────────────────────')
console.log('--- BROWSER CONSOLE (last 40) ---')
console.log(logs.slice(-40).join('\n') || '(no console output)')

await browser.close()
