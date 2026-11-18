import puppeteer from 'puppeteer-core'
import fs from 'node:fs'
import path from 'node:path'

const BASE = process.env.APP_URL || 'http://127.0.0.1:4173/tree-practice/'
const OUT = process.env.SHOT_DIR || '/cursor/stores/bc-c3547c92-c335-424a-b18a-835d918df6a6/media'

fs.mkdirSync(OUT, { recursive: true })

const browser = await puppeteer.launch({
  executablePath: '/usr/bin/google-chrome-stable',
  headless: true,
  args: ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'],
})
const page = await browser.newPage()
await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 2 })
await page.goto(BASE, { waitUntil: 'networkidle2', timeout: 120000 })
await page.click('button.btn--primary')
await page.waitForSelector('.practice')
await page.waitForSelector('.cm-wrapper')
// wait a beat for layout
await new Promise((r) => setTimeout(r, 800))

const topShot = path.join(OUT, 'practice-mobile-after-top.png')
await page.screenshot({ path: topShot, fullPage: false })
console.log('wrote', topShot)

const metrics = await page.evaluate(() => {
  const practice = document.querySelector('.practice')
  const statement = document.querySelector('.statement')
  const editor = document.querySelector('.editor-pane')
  const cm = document.querySelector('.cm-wrapper')
  const workspace = document.querySelector('.workspace')
  const scroller = document.querySelector('.cm-scroller')
  const body = document.body

  const cs = (el) => (el ? getComputedStyle(el) : null)
  const rect = (el) => {
    if (!el) return null
    const r = el.getBoundingClientRect()
    return { top: r.top, bottom: r.bottom, height: r.height, width: r.width }
  }

  return {
    viewport: { w: window.innerWidth, h: window.innerHeight },
    docScrollHeight: Math.max(
      body.scrollHeight,
      document.documentElement.scrollHeight,
    ),
    bodyOverflow: cs(body)?.overflow + '/' + cs(body)?.overflowY,
    practice: {
      height: cs(practice)?.height,
      maxHeight: cs(practice)?.maxHeight,
      overflow: cs(practice)?.overflow,
      rect: rect(practice),
    },
    workspace: {
      overflow: cs(workspace)?.overflowY,
      height: cs(workspace)?.height,
      scrollHeight: workspace?.scrollHeight,
      clientHeight: workspace?.clientHeight,
      rect: rect(workspace),
    },
    statement: {
      maxHeight: cs(statement)?.maxHeight,
      overflow: cs(statement)?.overflow,
      height: statement?.scrollHeight,
      rect: rect(statement),
      textSample: statement?.innerText?.slice(0, 180),
    },
    editor: {
      height: cs(editor)?.height,
      rect: rect(editor),
      belowStatement: (rect(editor)?.top ?? 0) >= (rect(statement)?.bottom ?? 0) - 2,
    },
    cm: {
      height: cs(cm)?.height,
      scrollerOverflow: cs(scroller)?.overflowY,
      scrollerScrollHeight: scroller?.scrollHeight,
      scrollerClientHeight: scroller?.clientHeight,
    },
    constraintsOpen: !!document.querySelector('.statement__constraints[open]'),
    hasCallout: !!document.querySelector('.statement__io-callout'),
  }
})
console.log('metrics', JSON.stringify(metrics, null, 2))

// Scroll page so editor is in view
await page.evaluate(() => {
  const editor = document.querySelector('.editor-pane')
  editor?.scrollIntoView({ block: 'start' })
})
await new Promise((r) => setTimeout(r, 400))
const editorShot = path.join(OUT, 'practice-mobile-after-editor.png')
await page.screenshot({ path: editorShot, fullPage: false })
console.log('wrote', editorShot)

// Try scrolling inside CodeMirror — starter is long, must overflow the pane
const cmScroll = await page.evaluate(() => {
  const scroller = document.querySelector('.cm-scroller')
  const pane = document.querySelector('.editor-pane')
  if (!scroller || !pane) return { ok: false, reason: 'no scroller/pane' }
  const paneH = pane.getBoundingClientRect().height
  const before = scroller.scrollTop
  scroller.scrollTop = 800
  const after = scroller.scrollTop
  const overflows = scroller.scrollHeight > scroller.clientHeight + 40
  return {
    ok: overflows && after > before,
    before,
    after,
    scrollHeight: scroller.scrollHeight,
    clientHeight: scroller.clientHeight,
    paneH,
    overflows,
  }
})
console.log('cmScroll', cmScroll)

// Scroll document to bottom
await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))
await new Promise((r) => setTimeout(r, 300))
const bottomShot = path.join(OUT, 'practice-mobile-after-bottom.png')
await page.screenshot({ path: bottomShot, fullPage: false })
console.log('wrote', bottomShot)

const fullShot = path.join(OUT, 'practice-mobile-after-full.png')
await page.screenshot({ path: fullShot, fullPage: true })
console.log('wrote', fullShot)

let failed = false
if (metrics.statement.maxHeight && metrics.statement.maxHeight !== 'none') {
  console.error('FAIL: statement still has max-height', metrics.statement.maxHeight)
  failed = true
}
if (!metrics.editor.belowStatement) {
  console.error('FAIL: editor not below statement')
  failed = true
}
if (metrics.docScrollHeight <= metrics.viewport.h + 40) {
  console.error('FAIL: document not taller than viewport — cannot page-scroll', metrics.docScrollHeight, metrics.viewport.h)
  failed = true
}
if (metrics.statement.height < 200) {
  console.error('FAIL: statement too short', metrics.statement.height)
  failed = true
}
if (!cmScroll.ok) {
  console.error('FAIL: CodeMirror cannot scroll', cmScroll)
  failed = true
}
if (metrics.constraintsOpen) {
  console.error('FAIL: constraints should start collapsed on mobile UX')
  failed = true
}

if (failed) process.exitCode = 1
else console.log('mobile layout OK')

await browser.close()
