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
  }
}
