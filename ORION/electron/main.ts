import { app, BrowserWindow, BrowserView, ipcMain, session, shell, DownloadItem } from 'electron'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { ElectronBlocker } from '@cliqz/adblocker-electron'
import fetch from 'cross-fetch'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// The built directory structure
process.env.APP_ROOT = path.join(__dirname, '..')

// 🚧 Use ['ENV_NAME'] avoid vite:define plugin - Vite@2.x
export const VITE_DEV_SERVER_URL = process.env['VITE_DEV_SERVER_URL']
export const MAIN_DIST = path.join(process.env.APP_ROOT, 'dist-electron')
export const RENDERER_DIST = path.join(process.env.APP_ROOT, 'dist')

process.env.VITE_PUBLIC = VITE_DEV_SERVER_URL ? path.join(process.env.APP_ROOT, 'public') : RENDERER_DIST

let win: BrowserWindow | null
let view: BrowserView | null = null
let isSidePanelOpen = true // Default state matching UI
// Map to store active download items by ID (we'll use startTime as a simple ID for now)
const downloadItems = new Map<string, DownloadItem>()

let blocker: ElectronBlocker | null = null
let shieldsActive = true

// CONSTANTS
const TOP_BAR_HEIGHT = 40
const OMNIBOX_HEIGHT = 50
const TOP_OFFSET = TOP_BAR_HEIGHT + OMNIBOX_HEIGHT
const SIDE_PANEL_WIDTH = 300

function updateViewBounds() {
  if (!win || !view) return

  const contentBounds = win.getContentBounds()

  // Calculate width based on side panel state
  const width = isSidePanelOpen
    ? contentBounds.width - SIDE_PANEL_WIDTH
    : contentBounds.width

  // Calculate height (subtract top offset)
  const height = contentBounds.height - TOP_OFFSET

  view.setBounds({
    x: 0,
    y: TOP_OFFSET,
    width: width,
    height: height
  })
}

function createBrowserView() {
  if (!win) return

  view = new BrowserView({
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    }
  })

  win.setBrowserView(view)

  // Initial bounds
  updateViewBounds()

  // Load default URL
  view.webContents.loadURL('https://google.com')

  // Events
  view.webContents.on('did-navigate', (_, url) => {
    win?.webContents.send('shell:url-change', url)
  })

  view.webContents.on('did-navigate-in-page', (_, url) => {
    win?.webContents.send('shell:url-change', url)
  })
}

function setupDownloadManager() {
  session.defaultSession.on('will-download', (_event, item, _webContents) => {
    const id = item.getStartTime().toString()
    downloadItems.set(id, item)

    const fileName = item.getFilename()
    const totalBytes = item.getTotalBytes()

    // Notify Renderer: Start
    win?.webContents.send('download:start', {
      id,
      filename: fileName,
      totalBytes
    })

    item.on('updated', (_event, state) => {
      if (state === 'interrupted') {
        win?.webContents.send('download:complete', {
          id,
          state: 'interrupted'
        })
      } else if (state === 'progressing') {
        if (item.isPaused()) {
           // Handle paused state if needed
        } else {
           win?.webContents.send('download:progress', {
             id,
             receivedBytes: item.getReceivedBytes(),
             totalBytes: item.getTotalBytes(),
             percentage: item.getTotalBytes() > 0 ? (item.getReceivedBytes() / item.getTotalBytes()) * 100 : 0
           })
        }
      }
    })

    item.once('done', (_event, state) => {
      downloadItems.delete(id)
      win?.webContents.send('download:complete', {
        id,
        state, // 'completed', 'cancelled', 'interrupted'
        path: item.getSavePath()
      })
    })
  })
}

async function setupAdBlocker() {
  try {
    blocker = await ElectronBlocker.fromPrebuiltAdsAndTracking(fetch)
    if (shieldsActive) {
      blocker.enableBlockingInSession(session.defaultSession)
    }
  } catch (error) {
    console.error('Failed to initialize ad blocker:', error)
  }
}

function createWindow() {
  win = new BrowserWindow({
    icon: path.join(process.env.VITE_PUBLIC, 'electron-vite.svg'),
    frame: false,
    titleBarStyle: 'hidden',
    webPreferences: {
      preload: path.join(__dirname, 'preload.mjs'),
    },
    width: 1200,
    height: 800
  })

  win.on('resize', () => {
    updateViewBounds()
  })

  if (VITE_DEV_SERVER_URL) {
    win.loadURL(VITE_DEV_SERVER_URL)
  } else {
    win.loadFile(path.join(RENDERER_DIST, 'index.html'))
  }

  // Initialize View after window is ready
  win.once('ready-to-show', () => {
    createBrowserView()
  })
}

// IPC Handlers
ipcMain.on('shell:navigate', (_, url) => {
  if (view) {
    // Basic protocol handling
    const targetUrl = url.startsWith('http') ? url : `https://${url}`
    view.webContents.loadURL(targetUrl)
  }
})

ipcMain.on('shell:back', () => {
  if (view && view.webContents.canGoBack()) {
    view.webContents.goBack()
  }
})

ipcMain.on('shell:forward', () => {
  if (view && view.webContents.canGoForward()) {
    view.webContents.goForward()
  }
})

ipcMain.on('shell:reload', () => {
    if (view) {
        view.webContents.reload()
    }
})

ipcMain.on('shell:resize-view', (_, sidePanelOpen) => {
  isSidePanelOpen = sidePanelOpen
  updateViewBounds()
})

// Chrome Parity Handlers
ipcMain.on('shell:zoom-in', () => {
  if (view) {
    const currentZoom = view.webContents.getZoomLevel()
    view.webContents.setZoomLevel(currentZoom + 0.5)
  }
})

ipcMain.on('shell:zoom-out', () => {
  if (view) {
    const currentZoom = view.webContents.getZoomLevel()
    view.webContents.setZoomLevel(currentZoom - 0.5)
  }
})

ipcMain.on('shell:zoom-reset', () => {
  if (view) {
    view.webContents.setZoomLevel(0)
  }
})

ipcMain.on('shell:print', () => {
  if (view) {
    view.webContents.print()
  }
})

ipcMain.on('shell:find-text', (_, text) => {
  if (view && text) {
    view.webContents.findInPage(text)
  }
})

ipcMain.on('shell:stop-find', () => {
  if (view) {
    view.webContents.stopFindInPage('clearSelection')
  }
})

ipcMain.on('shell:show-item', (_, fullPath) => {
  shell.showItemInFolder(fullPath)
})

ipcMain.on('shell:cancel-download', (_, id) => {
  const item = downloadItems.get(id)
  if (item) {
    item.cancel()
  }
})

ipcMain.handle('shell:get-shields-status', () => {
  return shieldsActive
})

ipcMain.on('shell:toggle-shields', () => {
  shieldsActive = !shieldsActive

  if (blocker) {
    if (shieldsActive) {
      blocker.enableBlockingInSession(session.defaultSession)
    } else {
      blocker.disableBlockingInSession(session.defaultSession)
    }
  }

  win?.webContents.send('shell:shields-update', shieldsActive)
  if (view) {
    view.webContents.reload() // Reload page to apply changes
  }
})

ipcMain.on('agent:perform-action', async (_, action) => {
  if (!view) return

  const { type, selector, value } = action
  // Sanitize input: JSON.stringify safely quotes the strings
  const safeSelector = JSON.stringify(selector)
  const safeValue = value ? JSON.stringify(value) : '""'
  let script = ''

  switch (type) {
    case 'click':
      script = `
        (() => {
          const el = document.querySelector(${safeSelector});
          if (el) {
            el.click();
            return { success: true };
          }
          return { success: false, error: 'Element not found' };
        })()
      `
      break
    case 'type':
      script = `
        (() => {
          const el = document.querySelector(${safeSelector});
          if (el) {
            el.value = ${safeValue};
            el.dispatchEvent(new Event('input', { bubbles: true }));
            return { success: true };
          }
          return { success: false, error: 'Element not found' };
        })()
      `
      break
    case 'scroll':
      script = `
        (() => {
          const el = document.querySelector(${safeSelector});
          if (el) {
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            return { success: true };
          }
          return { success: false, error: 'Element not found' };
        })()
      `
      break
  }

  if (script) {
    try {
      await view.webContents.executeJavaScript(script)
    } catch (e) {
      console.error('Agent action failed', e)
    }
  }
})

ipcMain.handle('agent:scan', async () => {
  if (!view) return null

  const script = `
    (() => {
      const getMetaContent = (name) => {
        const meta = document.querySelector(\`meta[name="\${name}"]\`);
        return meta ? meta.getAttribute('content') : '';
      };

      const getHeadings = () => {
        return Array.from(document.querySelectorAll('h1, h2, h3'))
          .map(h => h.innerText.trim())
          .filter(text => text.length > 0)
          .slice(0, 10);
      };

      // Improved interactive element scanning with unique selectors
      const getInteractive = () => {
        const getPath = (el) => {
          if (el.id) return '#' + el.id;
          if (el === document.body) return 'body';

          let path = [];
          while (el.parentNode) {
             let index = 0;
             let sibling = el;
             while ((sibling = sibling.previousElementSibling)) {
               if (sibling.tagName === el.tagName) index++;
             }
             path.unshift(el.tagName.toLowerCase() + (index > 0 ? \`:nth-of-type(\${index + 1})\` : ''));
             el = el.parentNode;
             if (el.id) {
               path.unshift('#' + el.id);
               break;
             }
             if (el === document.body) {
               path.unshift('body');
               break;
             }
          }
          return path.join(' > ');
        };

        return Array.from(document.querySelectorAll('button, a, input, [role="button"]'))
           .map(el => {
             const text = el.innerText ? el.innerText.trim() : el.value || el.placeholder || '';
             // Skip invisible or empty elements
             const rect = el.getBoundingClientRect();
             if (rect.width === 0 || rect.height === 0 || !text) return null;

             return {
               tag: el.tagName.toLowerCase(),
               text: text.substring(0, 50),
               selector: getPath(el),
               type: el.tagName === 'INPUT' ? 'input' : 'clickable'
             };
           })
           .filter(Boolean)
           .slice(0, 30); // Limit results
      };

      return {
        title: document.title,
        description: getMetaContent('description'),
        headings: getHeadings(),
        interactive: getInteractive()
      };
    })()
  `

  try {
    const data = await view.webContents.executeJavaScript(script)
    return data
  } catch (error) {
    console.error('Agent scan failed:', error)
    return { error: 'Failed to scan page' }
  }
})


app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
    win = null
    view = null
  }
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow()
  }
})

app.whenReady().then(async () => {
  await setupAdBlocker()
  createWindow()
  setupDownloadManager()
})
