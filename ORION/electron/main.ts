import { app, BrowserWindow, BrowserView, ipcMain } from 'electron'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

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

app.whenReady().then(createWindow)
