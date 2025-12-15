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
  scanPage: () => ipcRenderer.invoke('agent:scan')
})
