import { ipcRenderer, contextBridge } from 'electron'

// --------- Expose some API to the Renderer process ---------
contextBridge.exposeInMainWorld('electron', {
  navigate: (url: string) => ipcRenderer.send('shell:navigate', url),
  goBack: () => ipcRenderer.send('shell:back'),
  goForward: () => ipcRenderer.send('shell:forward'),
  reload: () => ipcRenderer.send('shell:reload'),
  resizeBrowserView: (sidePanelOpen: boolean) => ipcRenderer.send('shell:resize-view', sidePanelOpen),
  onUrlChange: (callback: (url: string) => void) => {
    ipcRenderer.on('shell:url-change', (_, url) => callback(url))
  },
  scanPage: () => ipcRenderer.invoke('agent:scan'),

  // Chrome Parity Features
  zoomIn: () => ipcRenderer.send('shell:zoom-in'),
  zoomOut: () => ipcRenderer.send('shell:zoom-out'),
  zoomReset: () => ipcRenderer.send('shell:zoom-reset'),
  printPage: () => ipcRenderer.send('shell:print'),
  findInPage: (text: string) => ipcRenderer.send('shell:find-text', text),
  stopFind: () => ipcRenderer.send('shell:stop-find')
})
