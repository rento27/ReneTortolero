/// <reference types="vite/client" />

interface Window {
  electron: {
    navigate: (url: string) => void
    goBack: () => void
    goForward: () => void
    reload: () => void
    resizeBrowserView: (sidePanelOpen: boolean) => void
    onUrlChange: (callback: (url: string) => void) => void
    scanPage: () => Promise<any>

    // Chrome Parity
    zoomIn: () => void
    zoomOut: () => void
    zoomReset: () => void
    printPage: () => void
    findInPage: (text: string) => void
    stopFind: () => void

    // Downloads
    showItemInFolder: (path: string) => void
    cancelDownload: (id: string) => void
    onDownloadStart: (callback: (data: any) => void) => void
    onDownloadProgress: (callback: (data: any) => void) => void
    onDownloadComplete: (callback: (data: any) => void) => void

    // AdBlock
    toggleShields: () => void
    getShieldsStatus: () => Promise<boolean>
    onShieldsUpdate: (callback: (active: boolean) => void) => void
  }
}
